import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypePrismPlus from 'rehype-prism-plus';
import { Send, Loader2, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { AskRequest, AskResponse, SelfLoopIteration } from '@/lib/api';
import { cn, formatDuration } from '@/lib/utils';
import IterationCard from './IterationCard';

interface ChatPanelSubmitHandlers {
  onIteration: (iteration: SelfLoopIteration) => void;
}

interface ChatPanelProps {
  onSubmit: (request: AskRequest, handlers: ChatPanelSubmitHandlers) => Promise<AskResponse>;
  isLoading: boolean;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  response?: AskResponse;
}

const createEmptyResponse = (): AskResponse => ({
  answer: '',
  citations: [],
  iterations: [],
  model_tier: null,
  retrieval_mode: 'disabled',
  duration_ms: null,
  rounds: 0,
});

export default function ChatPanel({ onSubmit, isLoading }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [expandedCitations, setExpandedCitations] = useState<Set<string>>(new Set());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    const userMessage: ChatMessage = {
      id: `${Date.now()}`,
      type: 'user',
      content: question,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    const assistantId = `${Date.now()}-assistant`;
    const placeholder: ChatMessage = {
      id: assistantId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      response: createEmptyResponse(),
    };
    setMessages(prev => [...prev, placeholder]);

    const handleIteration = (iteration: SelfLoopIteration) => {
      setMessages(prev =>
        prev.map(message => {
          if (message.id !== assistantId) return message;
          const response = message.response ?? createEmptyResponse();
          const alreadyExists = response.iterations.some(
            existing => existing.timestamp === iteration.timestamp && existing.step === iteration.step && existing.round === iteration.round,
          );
          if (alreadyExists) {
            return message;
          }
          return {
            ...message,
            response: {
              ...response,
              iterations: [...response.iterations, iteration],
            },
          };
        })
      );
    };

    try {
      const response = await onSubmit({ question }, { onIteration: handleIteration });
      setMessages(prev =>
        prev.map(message => {
          if (message.id !== assistantId) return message;
          return {
            ...message,
            content: response.answer,
            timestamp: new Date(),
            response: {
              ...response,
              iterations: response.iterations ?? [],
            },
          };
        })
      );
    } catch (error) {
      console.error('Error submitting question:', error);
      setMessages(prev =>
        prev.map(message => {
          if (message.id !== assistantId) return message;
          return {
            ...message,
            content: 'Sorry, I encountered an error processing your question. Please try again.',
            response: undefined,
          };
        })
      );
    }
  };

  const toggleCitation = (citationId: string) => {
    setExpandedCitations(prev => {
      const next = new Set(prev);
      if (next.has(citationId)) {
        next.delete(citationId);
      } else {
        next.add(citationId);
      }
      return next;
    });
  };

  const renderCitations = (citations: string[] | undefined) => {
    if (!citations || citations.length === 0) return null;
    return (
      <div className="mt-6 border-t border-gray-200/50 dark:border-gray-700/50 pt-5">
        <div className="flex items-center space-x-2 mb-4">
          <div className="h-1 w-1 bg-accent-500 rounded-full animate-pulse"></div>
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Sources ({citations.length})
          </h4>
          <div className="flex-1 h-px bg-gradient-to-r from-accent-200 to-transparent dark:from-accent-800"></div>
        </div>
        <div className="space-y-3">
          {citations.map((citation, index) => {
            const citationId = `${citation}-${index}`;
            const isExpanded = expandedCitations.has(citationId);
            return (
              <div
                key={citationId}
                className="glass-effect rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden hover:shadow-md transition-all duration-300"
              >
                <button
                  onClick={() => toggleCitation(citationId)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gradient-to-r hover:from-primary-50/50 hover:to-accent-50/50 dark:hover:from-gray-700/50 dark:hover:to-gray-600/50 transition-all duration-200 group"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <span className="flex-shrink-0 text-xs font-bold bg-gradient-to-r from-primary-600 to-accent-600 text-white px-3 py-1.5 rounded-lg shadow-sm">
                      [{index + 1}]
                    </span>
                    <span className="text-sm text-gray-700 dark:text-gray-300 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                      {citation}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                    <ExternalLink className="h-4 w-4 text-gray-400 group-hover:text-primary-500 transition-colors" />
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors" />
                    )}
                  </div>
                </button>
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-200/50 dark:border-gray-700/50 animate-slide-down">
                    <div className="mt-3 text-xs text-gray-600 dark:text-gray-400 bg-gray-50/50 dark:bg-gray-800/50 p-3 rounded-lg">
                      <p className="mb-2 text-gray-500 dark:text-gray-500 italic">Source preview would be displayed here in a production system.</p>
                      <p className="font-mono text-primary-600 dark:text-primary-400 break-all">{citation}</p>
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
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full animate-fade-in">
            <div className="text-center max-w-2xl px-6">
              <div className="relative inline-block mb-6">
                <div className="absolute inset-0 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full blur-2xl opacity-30 animate-pulse"></div>
                <div className="relative text-7xl animate-bounce-subtle">🤖</div>
              </div>
              <h2 className="text-4xl font-bold mb-4">
                <span className="gradient-text">Welcome to LIQUID-SQUAD</span>
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
                Powered by self-loop reasoning with <span className="font-semibold text-primary-600 dark:text-primary-400">plan → draft → critic → verify → revise</span> cycles
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="glass-effect p-4 rounded-2xl hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="text-3xl mb-2">🧠</div>
                  <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Multi-Tier Models</h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Intelligent model routing</p>
                </div>
                <div className="glass-effect p-4 rounded-2xl hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="text-3xl mb-2">🔄</div>
                  <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Self-Loop Logic</h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Iterative refinement</p>
                </div>
                <div className="glass-effect p-4 rounded-2xl hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                  <div className="text-3xl mb-2">📚</div>
                  <h3 className="font-semibold text-sm text-gray-900 dark:text-gray-100">Hybrid RAG</h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Dense + sparse retrieval</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, idx) => {
          const isUser = message.type === 'user';
          const iterations = message.response?.iterations ?? [];
          const hasAnswer = Boolean(message.content);
          return (
            <div
              key={message.id}
              className={cn(
                'flex animate-slide-up',
                isUser ? 'justify-end' : 'justify-start'
              )}
              style={{ animationDelay: `${idx * 0.1}s` }}
            >
              <div
                className={cn(
                  'max-w-3xl rounded-2xl px-5 py-4 shadow-lg transition-all duration-300 hover:shadow-xl',
                  isUser
                    ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white'
                    : 'glass-effect border border-gray-200/50 dark:border-gray-700/50'
                )}
              >
                {isUser ? (
                  <div className="flex items-start space-x-3">
                    <div className="flex-1">
                      <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    {iterations.length > 0 && (
                      <div className="mb-6">
                        <div className="flex items-center space-x-2 mb-4">
                          <div className="h-1 w-1 bg-primary-500 rounded-full animate-pulse"></div>
                          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                            Self-Loop Process
                          </h3>
                          <div className="flex-1 h-px bg-gradient-to-r from-primary-200 to-transparent dark:from-primary-800"></div>
                        </div>
                        <div className="space-y-3">
                          {iterations.map((iteration, index) => (
                            <IterationCard
                              key={`${message.id}-iteration-${index}`}
                              iteration={iteration}
                              index={index}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {hasAnswer ? (
                        <div className="animate-fade-in">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex, rehypePrismPlus]}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-3 text-sm text-gray-500 dark:text-gray-400 py-2">
                          <div className="relative">
                            <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                            <div className="absolute inset-0 bg-primary-500/20 rounded-full blur-md animate-pulse"></div>
                          </div>
                          <span className="animate-pulse">Generating answer...</span>
                        </div>
                      )}
                    </div>

                    {renderCitations(message.response?.citations)}

                    {message.response && (
                      <div className="mt-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
                        <div className="flex flex-wrap items-center gap-2">
                          {message.response.model_tier && (
                            <span className="px-2.5 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-medium rounded-lg">
                              {message.response.model_tier}
                            </span>
                          )}
                          {message.response.retrieval_mode && (
                            <span className="px-2.5 py-1 bg-accent-100 dark:bg-accent-900/30 text-accent-700 dark:text-accent-300 text-xs font-medium rounded-lg">
                              {message.response.retrieval_mode}
                            </span>
                          )}
                          {typeof message.response.duration_ms === 'number' && message.response.duration_ms >= 0 && (
                            <span className="px-2.5 py-1 bg-gray-100 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 text-xs font-medium rounded-lg">
                              ⏱️ {formatDuration(message.response.duration_ms)}
                            </span>
                          )}
                          {message.response.rounds > 0 && (
                            <span className="px-2.5 py-1 bg-gray-100 dark:bg-gray-700/50 text-gray-700 dark:text-gray-300 text-xs font-medium rounded-lg">
                              🔄 {message.response.rounds} rounds
                            </span>
                          )}
                          <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-gray-200/50 dark:border-gray-700/50 p-6 glass-effect">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <div className="relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                rows={3}
                className="input-field resize-none pr-12"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              {input.trim() && (
                <div className="absolute bottom-3 right-3 text-xs text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-800 px-2 py-1 rounded-md">
                  {input.length} chars
                </div>
              )}
            </div>
            <div className="mt-2 flex items-center justify-between">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                <kbd className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600 text-xs">Enter</kbd> to send, <kbd className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600 text-xs">Shift+Enter</kbd> for new line
              </p>
            </div>
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-primary self-start flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed h-fit"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                <span>Send</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
