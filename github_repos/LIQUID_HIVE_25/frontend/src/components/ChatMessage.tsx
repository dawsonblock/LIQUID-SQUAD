import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { User, Sparkles, Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Message } from '@/lib/store';
import { cn, formatTimestamp } from '@/lib/utils';
import { useChatStore } from '@/lib/store';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = React.useState(false);
  const { settings } = useChatStore();
  const isUser = message.role === 'user';

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyMessage = async () => {
    await handleCopy(message.content);
  };

  return (
    <div
      className={cn(
        'group flex gap-4 px-6 py-6 transition-colors animate-fade-in',
        isUser ? 'bg-transparent' : 'bg-gray-50/50 dark:bg-gray-800/30'
      )}
      data-testid={`message-${message.role}`}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div
          className={cn(
            'w-10 h-10 rounded-full flex items-center justify-center shadow-md',
            isUser
              ? 'bg-gradient-to-br from-primary-500 to-purple-600'
              : 'bg-gradient-to-br from-purple-500 to-pink-600'
          )}
        >
          {isUser ? (
            <User size={20} className="text-white" />
          ) : (
            <Sparkles size={20} className="text-white" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {isUser ? 'You' : 'LIQUID HIVE'}
          </span>
          {settings.showTimestamps && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatTimestamp(message.timestamp)}
            </span>
          )}
        </div>

        <div className={cn(
          'prose prose-sm dark:prose-invert max-w-none',
          settings.fontSize === 'small' && 'text-sm',
          settings.fontSize === 'large' && 'text-lg'
        )}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const codeString = String(children).replace(/\n$/, '');
                const isInline = !match;

                return !isInline && match ? (
                  <div className="relative group/code my-4">
                    <div className="flex items-center justify-between px-4 py-2 bg-gray-800 dark:bg-gray-900 rounded-t-xl border-b border-gray-700">
                      <span className="text-xs font-mono text-gray-400">{match[1]}</span>
                      <button
                        onClick={() => handleCopy(codeString)}
                        className="flex items-center gap-1 px-2 py-1 rounded-md bg-gray-700 hover:bg-gray-600 transition-colors text-xs text-gray-300"
                        data-testid="copy-code-button"
                      >
                        {copied ? (
                          <>
                            <Check size={14} className="text-green-400" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={14} />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    <SyntaxHighlighter
                      style={settings.codeTheme === 'dark' ? vscDarkPlus : vs}
                      language={match[1]}
                      PreTag="div"
                      className="!mt-0 !rounded-t-none"
                      showLineNumbers
                    >
                      {codeString}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className={cn(
                    className,
                    'px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-sm font-mono'
                  )}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <p className="text-xs font-semibold text-blue-900 dark:text-blue-200 mb-2 flex items-center gap-2">
              <span>📚</span> Sources
            </p>
            <ul className="text-xs text-blue-800 dark:text-blue-300 space-y-1">
              {message.citations.map((citation, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="font-semibold">[{idx + 1}]</span>
                  <span>{citation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        {!isUser && (
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-2">
            <button
              onClick={handleCopyMessage}
              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Copy message"
              data-testid="copy-message-button"
            >
              <Copy size={16} className="text-gray-600 dark:text-gray-400" />
            </button>
            <button
              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Good response"
              data-testid="thumbs-up-button"
            >
              <ThumbsUp size={16} className="text-gray-600 dark:text-gray-400" />
            </button>
            <button
              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
              title="Bad response"
              data-testid="thumbs-down-button"
            >
              <ThumbsDown size={16} className="text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};