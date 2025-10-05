import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
import { ThemeToggle } from '@/components/ThemeToggle';
import { SettingsPanel } from '@/components/SettingsPanel';
import { CommandPalette } from '@/components/CommandPalette';
import { ToastContainer, ToastProps } from '@/components/Toast';
import { useChatStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { Sparkles } from 'lucide-react';

export default function Home() {
  const {
    conversations,
    currentConversationId,
    isLoading,
    error,
    createConversation,
    addMessage,
    deleteConversation,
    setCurrentConversation,
    setLoading,
    setError,
    clearError,
    uiState,
  } = useChatStore();

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const addToast = (type: ToastProps['type'], message: string) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newToast: ToastProps = {
      id,
      type,
      message,
      onClose: (id) => setToasts((prev) => prev.filter((t) => t.id !== id)),
    };
    setToasts((prev) => [...prev, newToast]);
  };

  useEffect(() => {
    // Check authentication on mount
    const checkAuth = async () => {
      try {
        await apiClient.health();
        setIsAuthenticated(true);
        addToast('success', 'Connected to LIQUID HIVE');
      } catch (err) {
        console.error('Authentication check failed:', err);
        // For demo purposes, create a demo token
        try {
          const { token } = await apiClient.createToken('demo_user');
          apiClient.setToken(token);
          setIsAuthenticated(true);
          addToast('info', 'Demo session started');
        } catch (tokenErr) {
          console.error('Failed to create demo token:', tokenErr);
          addToast('error', 'Failed to connect to LIQUID HIVE');
        }
      }
    };

    checkAuth();
  }, []);

  useEffect(() => {
    // Create initial conversation if none exists
    if (conversations.length === 0 && isAuthenticated) {
      createConversation('Welcome Chat');
    }
  }, [conversations.length, createConversation, isAuthenticated]);

  const handleNewConversation = () => {
    createConversation();
    addToast('success', 'New conversation created');
  };

  const handleSelectConversation = (id: string) => {
    setCurrentConversation(id);
  };

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id);
    addToast('success', 'Conversation deleted');
  };

  const handleSendMessage = async (content: string) => {
    if (!currentConversationId) {
      const newConvId = createConversation();
      setCurrentConversation(newConvId);
    }

    const convId = currentConversationId || conversations[0]?.id;
    if (!convId) return;

    // Add user message
    addMessage(convId, {
      role: 'user',
      content,
    });

    // Set loading state
    setLoading(true);
    clearError();

    try {
      // Call API
      const response = await apiClient.ask(content);

      // Add assistant response
      addMessage(convId, {
        role: 'assistant',
        content: response.answer,
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to get response';
      setError(errorMessage);
      addToast('error', errorMessage);

      // Add error message to chat
      addMessage(convId, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const currentConversation = conversations.find(
    (conv) => conv.id === currentConversationId
  );

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-primary-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="relative mb-8 inline-flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-purple-600 rounded-full blur-2xl opacity-50 animate-pulse-slow" />
            <div className="relative w-24 h-24 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center shadow-2xl">
              <Sparkles size={48} className="text-white animate-pulse" />
            </div>
          </div>
          <h1 className="text-3xl font-bold mb-4 gradient-text">Connecting to LIQUID HIVE...</h1>
          <div className="flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>LIQUID HIVE 25 - Advanced Multi-Tier LLM System</title>
        <meta name="description" content="Advanced Multi-Tier LLM System with Self-Loop Reasoning & Hybrid RAG" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Top Bar */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              {!uiState.isSidebarOpen && (
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                    <Sparkles size={18} className="text-white" />
                  </div>
                  <h1 className="text-lg font-bold gradient-text">LIQUID HIVE</h1>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <button
                onClick={() => addToast('info', 'Command palette: Press Cmd/Ctrl + K')}
                className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              >
                ⌘K
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 px-6 py-3">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Chat Container */}
          <ChatContainer
            messages={currentConversation?.messages || []}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>

        {/* Modals & Overlays */}
        <SettingsPanel />
        <CommandPalette />
        <ToastContainer toasts={toasts} />
      </div>
    </>
  );
}