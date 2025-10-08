"""
Conversation history and context management.

This module provides conversation tracking, context window management,
and multi-turn dialogue support for the self-loop system.
"""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Deque, Dict, List, Optional
from uuid import uuid4


@dataclass
class Turn:
    """A single conversation turn (question + answer)."""

    turn_id: str
    question: str
    answer: str
    citations: List[str]
    model_tier: str
    rounds: int
    duration_ms: int
    timestamp: float
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Conversation:
    """A conversation consisting of multiple turns."""

    conversation_id: str
    user_id: str
    turns: Deque[Turn]
    created_at: float
    updated_at: float
    max_turns: int = 10

    def add_turn(
        self,
        question: str,
        answer: str,
        citations: List[str],
        model_tier: str,
        rounds: int,
        duration_ms: int,
        metadata: Optional[Dict] = None,
    ) -> Turn:
        """Add a new turn to the conversation."""
        turn = Turn(
            turn_id=str(uuid4()),
            question=question,
            answer=answer,
            citations=citations,
            model_tier=model_tier,
            rounds=rounds,
            duration_ms=duration_ms,
            timestamp=time.time(),
            metadata=metadata,
        )

        self.turns.append(turn)
        self.updated_at = time.time()

        # Trim old turns if exceeding max
        while len(self.turns) > self.max_turns:
            self.turns.popleft()

        return turn

    def get_context(self, max_turns: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation context as a list of messages for the model.

        Args:
            max_turns: Maximum number of recent turns to include

        Returns:
            List of message dictionaries with role and content
        """
        turns_to_include = max_turns or len(self.turns)
        recent_turns = list(self.turns)[-turns_to_include:]

        messages = []
        for turn in recent_turns:
            messages.append({"role": "user", "content": turn.question})
            messages.append({"role": "assistant", "content": turn.answer})

        return messages

    def get_summary(self) -> Dict:
        """Get a summary of the conversation."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "turn_count": len(self.turns),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration_seconds": self.updated_at - self.created_at,
        }

    def to_dict(self) -> Dict:
        """Convert conversation to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "turns": [turn.to_dict() for turn in self.turns],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "max_turns": self.max_turns,
        }

    def to_json(self) -> str:
        """Export conversation as JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ConversationManager:
    """Manager for multiple conversations with memory limits."""

    def __init__(
        self,
        max_conversations: int = 100,
        max_turns_per_conversation: int = 10,
        ttl_seconds: float = 3600.0,
    ) -> None:
        """
        Initialize the conversation manager.

        Args:
            max_conversations: Maximum number of conversations to keep in memory
            max_turns_per_conversation: Maximum turns per conversation
            ttl_seconds: Time-to-live for inactive conversations (default 1 hour)
        """
        self.max_conversations = max_conversations
        self.max_turns_per_conversation = max_turns_per_conversation
        self.ttl_seconds = ttl_seconds
        self._conversations: Dict[str, Conversation] = {}
        self._user_conversations: Dict[str, List[str]] = {}
        self._lock = Lock()

    def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for a user."""
        conversation_id = str(uuid4())

        with self._lock:
            conversation = Conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                turns=deque(maxlen=self.max_turns_per_conversation),
                created_at=time.time(),
                updated_at=time.time(),
                max_turns=self.max_turns_per_conversation,
            )

            self._conversations[conversation_id] = conversation

            # Track user's conversations
            if user_id not in self._user_conversations:
                self._user_conversations[user_id] = []
            self._user_conversations[user_id].append(conversation_id)

            # Prune old conversations if needed
            self._prune_if_needed()

            return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        with self._lock:
            conversation = self._conversations.get(conversation_id)

            # Check if conversation has expired
            if conversation and self._is_expired(conversation):
                self._delete_conversation(conversation_id)
                return None

            return conversation

    def get_or_create_conversation(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> Conversation:
        """Get an existing conversation or create a new one."""
        if conversation_id:
            conversation = self.get_conversation(conversation_id)
            if conversation:
                return conversation

        return self.create_conversation(user_id)

    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user."""
        with self._lock:
            conversation_ids = self._user_conversations.get(user_id, [])
            conversations = []

            for conv_id in conversation_ids:
                conversation = self._conversations.get(conv_id)
                if conversation and not self._is_expired(conversation):
                    conversations.append(conversation)

            return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        with self._lock:
            return self._delete_conversation(conversation_id)

    def _delete_conversation(self, conversation_id: str) -> bool:
        """Internal delete without lock (assumes lock is held)."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return False

        # Remove from user's conversation list
        user_conversations = self._user_conversations.get(conversation.user_id, [])
        if conversation_id in user_conversations:
            user_conversations.remove(conversation_id)

        # Remove conversation
        del self._conversations[conversation_id]
        return True

    def _is_expired(self, conversation: Conversation) -> bool:
        """Check if a conversation has expired."""
        age = time.time() - conversation.updated_at
        return age > self.ttl_seconds

    def _prune_if_needed(self) -> None:
        """Prune old conversations if exceeding max (assumes lock is held)."""
        if len(self._conversations) <= self.max_conversations:
            return

        # Sort by last update time and remove oldest
        sorted_conversations = sorted(
            self._conversations.items(),
            key=lambda x: x[1].updated_at,
        )

        to_remove = len(self._conversations) - self.max_conversations
        for conv_id, _ in sorted_conversations[:to_remove]:
            self._delete_conversation(conv_id)

    def prune_expired(self) -> int:
        """Remove all expired conversations and return count."""
        with self._lock:
            expired_ids = [
                conv_id
                for conv_id, conv in self._conversations.items()
                if self._is_expired(conv)
            ]

            for conv_id in expired_ids:
                self._delete_conversation(conv_id)

            return len(expired_ids)

    def stats(self) -> Dict:
        """Get statistics about conversations."""
        with self._lock:
            total_turns = sum(
                len(conv.turns) for conv in self._conversations.values()
            )
            active_users = len(self._user_conversations)

            return {
                "total_conversations": len(self._conversations),
                "total_turns": total_turns,
                "active_users": active_users,
                "max_conversations": self.max_conversations,
            }


# Global conversation manager instance
_global_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = ConversationManager()
    return _global_manager


def configure_conversation_manager(
    max_conversations: int = 100,
    max_turns_per_conversation: int = 10,
    ttl_seconds: float = 3600.0,
) -> None:
    """Configure the global conversation manager."""
    global _global_manager
    _global_manager = ConversationManager(
        max_conversations=max_conversations,
        max_turns_per_conversation=max_turns_per_conversation,
        ttl_seconds=ttl_seconds,
    )
