
import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { Sidebar } from '@/components/Sidebar';
import { ChatContainer } from '@/components/ChatContainer';
import { useChatStore } from '@/lib/store';
import { apiClient } from '@/lib/api';

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
  } = useChatStore();

  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check authentication on mount
    const checkAuth = async () => {
      try {
        await apiClient.health();
        setIsAuthenticated(true);
      } catch (err) {
        console.error('Authentication check failed:', err);
        // For demo purposes, create a demo token
        try {
          const { token } = await apiClient.createToken('demo_user');
          apiClient.setToken(token);
          setIsAuthenticated(true);
        } catch (tokenErr) {
          console.error('Failed to create demo token:', tokenErr);
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
  };

  const handleSelectConversation = (id: string) => {
    setCurrentConversation(id);
  };

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id);
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
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Connecting to LIQUID HIVE...</h1>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>LIQUID HIVE 25 - Advanced Multi-Tier LLM System</title>
      </Head>

      <div className="flex h-screen overflow-hidden">
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        <div className="flex-1 flex flex-col">
          {error && (
            <div className="bg-red-50 border-b border-red-200 px-4 py-3 text-red-800">
              <p className="text-sm">{error}</p>
            </div>
          )}

          <ChatContainer
            messages={currentConversation?.messages || []}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>
    </>
  );
}
