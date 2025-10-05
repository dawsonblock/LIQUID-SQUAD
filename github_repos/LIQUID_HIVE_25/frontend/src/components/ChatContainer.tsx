import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { SuggestedPrompts } from './SuggestedPrompts';
import { Message } from '@/lib/store';
import { Sparkles } from 'lucide-react';

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
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handlePromptSelect = (prompt: string) => {
    onSendMessage(prompt);
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900" data-testid="chat-container">
      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4 py-12">
            {/* Welcome Header */}
            <div className="text-center mb-12 animate-fade-in">
              <div className="mb-6 inline-flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-purple-600 rounded-full blur-xl opacity-50 animate-pulse-slow" />
                  <div className="relative w-20 h-20 bg-gradient-to-br from-primary-500 to-purple-600 rounded-full flex items-center justify-center shadow-2xl">
                    <Sparkles size={40} className="text-white" />
                  </div>
                </div>
              </div>
              <h1 className="text-4xl md:text-5xl font-bold mb-4 gradient-text">
                Welcome to LIQUID HIVE
              </h1>
              <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Advanced Multi-Tier LLM System with Self-Loop Reasoning & Hybrid RAG
              </p>
            </div>

            {/* Suggested Prompts */}
            <div className="w-full max-w-4xl px-4">
              <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 text-center">
                Try one of these prompts to get started
              </p>
              <SuggestedPrompts onSelectPrompt={handlePromptSelect} />
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto mt-12 px-4">
              <div className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border border-blue-200 dark:border-blue-800">
                <div className="text-2xl mb-2">🧠</div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Self-Loop Reasoning</h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Iterative plan → draft → critic → revise cycles for better answers
                </p>
              </div>
              <div className="p-4 rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
                <div className="text-2xl mb-2">⚡</div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Multi-Tier Models</h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Intelligent failover between local and remote LLM endpoints
                </p>
              </div>
              <div className="p-4 rounded-xl bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 border border-green-200 dark:border-green-800">
                <div className="text-2xl mb-2">📚</div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Hybrid RAG</h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Dual indexing with Qdrant vectors + Elasticsearch BM25
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="max-w-4xl mx-auto w-full">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </div>
            
            {/* Loading State */}
            {isLoading && (
              <div className="max-w-4xl mx-auto w-full px-6 py-6 bg-gray-50/50 dark:bg-gray-800/30 animate-fade-in">
                <div className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-md animate-pulse">
                      <Sparkles size={20} className="text-white" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-gray-100">LIQUID HIVE</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">is thinking...</span>
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 shimmer" />
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 shimmer" />
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={onSendMessage}
            disabled={isLoading}
            placeholder="Ask LIQUID HIVE anything..."
          />
        </div>
      </div>
    </div>
  );
};