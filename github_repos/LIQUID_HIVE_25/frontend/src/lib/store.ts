import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  citations?: string[];
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export type Theme = 'light' | 'dark' | 'system';

export interface Settings {
  theme: Theme;
  fontSize: 'small' | 'medium' | 'large';
  codeTheme: 'dark' | 'light';
  sendOnEnter: boolean;
  showTimestamps: boolean;
}

interface UIState {
  isSidebarOpen: boolean;
  isSettingsOpen: boolean;
  isCommandPaletteOpen: boolean;
  searchQuery: string;
}

interface ChatStore {
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  error: string | null;
  settings: Settings;
  uiState: UIState;
  
  // Actions
  createConversation: (title?: string) => string;
  addMessage: (conversationId: string, message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (conversationId: string, messageId: string, content: string) => void;
  deleteConversation: (conversationId: string) => void;
  setCurrentConversation: (conversationId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // Settings actions
  updateSettings: (settings: Partial<Settings>) => void;
  
  // UI actions
  toggleSidebar: () => void;
  toggleSettings: () => void;
  toggleCommandPalette: () => void;
  setSearchQuery: (query: string) => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      error: null,
      settings: {
        theme: 'system',
        fontSize: 'medium',
        codeTheme: 'dark',
        sendOnEnter: true,
        showTimestamps: true,
      },
      uiState: {
        isSidebarOpen: true,
        isSettingsOpen: false,
        isCommandPaletteOpen: false,
        searchQuery: '',
      },

      createConversation: (title = 'New Conversation') => {
        const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const conversation: Conversation = {
          id,
          title,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          currentConversationId: id,
        }));
        
        return id;
      },

      addMessage: (conversationId, message) => {
        const messageWithMeta: Message = {
          ...message,
          id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now(),
        };

        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, messageWithMeta],
                  updatedAt: Date.now(),
                  title: conv.messages.length === 0 ? message.content.slice(0, 50) : conv.title,
                }
              : conv
          ),
        }));
      },

      updateMessage: (conversationId, messageId, content) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === messageId ? { ...msg, content } : msg
                  ),
                  updatedAt: Date.now(),
                }
              : conv
          ),
        }));
      },

      deleteConversation: (conversationId) => {
        set((state) => ({
          conversations: state.conversations.filter((conv) => conv.id !== conversationId),
          currentConversationId:
            state.currentConversationId === conversationId ? null : state.currentConversationId,
        }));
      },

      setCurrentConversation: (conversationId) => {
        set({ currentConversationId: conversationId });
      },

      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      setError: (error) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },

      updateSettings: (newSettings) => {
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        }));
      },

      toggleSidebar: () => {
        set((state) => ({
          uiState: { ...state.uiState, isSidebarOpen: !state.uiState.isSidebarOpen },
        }));
      },

      toggleSettings: () => {
        set((state) => ({
          uiState: { ...state.uiState, isSettingsOpen: !state.uiState.isSettingsOpen },
        }));
      },

      toggleCommandPalette: () => {
        set((state) => ({
          uiState: { ...state.uiState, isCommandPaletteOpen: !state.uiState.isCommandPaletteOpen },
        }));
      },

      setSearchQuery: (query) => {
        set((state) => ({
          uiState: { ...state.uiState, searchQuery: query },
        }));
      },

      setSidebarOpen: (open) => {
        set((state) => ({
          uiState: { ...state.uiState, isSidebarOpen: open },
        }));
      },
    }),
    {
      name: 'liquid-hive-storage',
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        settings: state.settings,
      }),
    }
  )
);