
import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { Message } from '@/lib/store';
import { Loader2 } from 'lucide-react';

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  onSendMessage,
  isLoading,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <h2 className="text-2xl font-bold mb-2">Welcome to LIQUID HIVE 25</h2>
              <p className="text-sm">
                Ask me anything about your documents, code, or general knowledge.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 size={20} className="animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={onSendMessage}
            disabled={isLoading}
            placeholder="Ask me anything..."
          />
        </div>
      </div>
    </div>
  );
};
