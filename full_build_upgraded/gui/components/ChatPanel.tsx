import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypePrismPlus from 'rehype-prism-plus';
import { Send, Loader2, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { AskRequest, AskResponse } from '@/lib/api';
import { cn } from '@/lib/utils';
import IterationCard from './IterationCard';

interface ChatPanelProps {
  onSubmit: (request: AskRequest) => Promise<AskResponse>;
  isLoading: boolean;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  response?: AskResponse;
}

export default function ChatPanel({ onSubmit, isLoading }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [expandedCitations, setExpandedCitations] = useState<Set<string>>(new Set());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await onSubmit({ question: input.trim() });
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        response,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error submitting question:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const toggleCitation = (citationId: string) => {
    setExpandedCitations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(citationId)) {
        newSet.delete(citationId);
      } else {
        newSet.add(citationId);
      }
      return newSet;
    });
  };

  const renderCitations = (citations: string[]) => {
    if (!citations || citations.length === 0) return null;

    return (
      <div className="mt-4 border-t border-gray-200 dark:border-gray-700 pt-4">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Sources ({citations.length})
        </h4>
        <div className="space-y-2">
          {citations.map((citation, index) => {
            const citationId = `${citation}-${index}`;
            const isExpanded = expandedCitations.has(citationId);
            
            return (
              <div
                key={citationId}
                className="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <button
                  onClick={() => toggleCitation(citationId)}
                  className="w-full px-3 py-2 flex items-center justify-between text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 px-2 py-1 rounded">
                      [{index + 1}]
                    </span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                      {citation}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <ExternalLink className="h-3 w-3 text-gray-400" />
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                </button>
                
                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                      <p>Source preview would be displayed here in a production system.</p>
                      <p className="mt-1 font-mono">{citation}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🤖</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Welcome to LIQUID-SQUAD
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              Ask me anything! I'll use self-loop reasoning with plan → draft → critic → verify → revise cycles to provide you with the best possible answer.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex',
              message.type === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'max-w-3xl rounded-lg px-4 py-3',
                message.type === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
              )}
            >
              {message.type === 'user' ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <div>
                  {/* Self-loop iterations */}
                  {message.response?.iterations && message.response.iterations.length > 0 && (
                    <div className="mb-6">
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Self-Loop Process
                      </h3>
                      <div className="space-y-3">
                        {message.response.iterations.map((iteration, index) => (
                          <IterationCard
                            key={`${message.id}-iteration-${index}`}
                            iteration={iteration}
                            index={index}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Final answer */}
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex, rehypePrismPlus]}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* Citations */}
                  {message.response?.citations && renderCitations(message.response.citations)}

                  {/* Metadata */}
                  {message.response && (
                    <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-4">
                      {message.response.model_tier && (
                        <span>Model: {message.response.model_tier}</span>
                      )}
                      {message.response.retrieval_mode && (
                        <span>Retrieval: {message.response.retrieval_mode}</span>
                      )}
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary-600" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Processing your question...
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input form */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-6">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              rows={3}
              className="input-field resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-primary self-start flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  );
}