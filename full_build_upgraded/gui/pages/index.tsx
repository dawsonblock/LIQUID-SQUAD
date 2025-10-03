import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { toast } from 'react-hot-toast';
import Layout from '@/components/Layout';
import ChatPanel from '@/components/ChatPanel';
import { createAPI, getAPI, AskRequest, AskResponse } from '@/lib/api';
import { getStoredAuthToken } from '@/lib/utils';

export default function Home() {
  const [modelTier, setModelTier] = useState('auto');
  const [retrievalMode, setRetrievalMode] = useState('disabled');
  const [criticEnabled, setCriticEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Initialize API
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const authToken = getStoredAuthToken();
    
    createAPI({
      baseURL: apiUrl,
      authToken: authToken || undefined,
    });
  }, []);

  const handleAskQuestion = async (request: AskRequest): Promise<AskResponse> => {
    setIsLoading(true);
    
    try {
      const api = getAPI();
      
      // Update auth token if it changed
      const currentToken = getStoredAuthToken();
      if (currentToken) {
        api.setAuthToken(currentToken);
      }
      
      const response = await api.ask(request);
      
      toast.success('Question answered successfully!');
      return response;
    } catch (error: any) {
      console.error('Error asking question:', error);
      
      if (error.response?.status === 401) {
        toast.error('Authentication failed. Please check your auth token.');
      } else if (error.response?.status === 429) {
        toast.error('Rate limit exceeded. Please wait before asking another question.');
      } else {
        toast.error('Failed to get answer. Please try again.');
      }
      
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>LIQUID-SQUAD - AI Agent Chat</title>
        <meta name="description" content="Chat with the LIQUID-SQUAD AI agent system" />
      </Head>

      <Layout
        modelTier={modelTier}
        onModelTierChange={setModelTier}
        retrievalMode={retrievalMode}
        onRetrievalModeChange={setRetrievalMode}
        criticEnabled={criticEnabled}
        onCriticToggle={setCriticEnabled}
      >
        <ChatPanel
          onSubmit={handleAskQuestion}
          isLoading={isLoading}
        />
      </Layout>
    </>
  );
}