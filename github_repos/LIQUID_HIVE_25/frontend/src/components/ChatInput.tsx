import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, StopCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/lib/store';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Ask LIQUID HIVE anything...',
}) => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { settings } = useChatStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 200);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (settings.sendOnEnter && e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative flex items-end gap-2 p-2 rounded-2xl bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
        {/* File Upload Button */}
        <button
          type="button"
          className="flex-shrink-0 p-2.5 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
          title="Attach file"
          disabled={disabled}
          data-testid="attach-file-button"
        >
          <Paperclip size={20} />
        </button>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className={cn(
            'flex-1 px-2 py-2.5 bg-transparent resize-none overflow-hidden',
            'focus:outline-none text-gray-900 dark:text-gray-100',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'placeholder:text-gray-400 dark:placeholder:text-gray-500'
          )}
          style={{ maxHeight: '200px' }}
          data-testid="chat-input-textarea"
        />

        {/* Voice Recording Button */}
        <button
          type="button"
          onClick={toggleRecording}
          className={cn(
            'flex-shrink-0 p-2.5 rounded-xl transition-all',
            isRecording
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
          )}
          title={isRecording ? 'Stop recording' : 'Start voice input'}
          disabled={disabled}
          data-testid="voice-input-button"
        >
          {isRecording ? <StopCircle size={20} /> : <Mic size={20} />}
        </button>

        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className={cn(
            'flex-shrink-0 p-2.5 rounded-xl transition-all flex items-center justify-center',
            input.trim() && !disabled
              ? 'bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
          )}
          data-testid="send-message-button"
        >
          <Send size={20} />
        </button>
      </div>

      {/* Helper Text */}
      <div className="flex items-center justify-center mt-2 text-xs text-gray-500 dark:text-gray-400">
        {settings.sendOnEnter ? (
          <span>Press Enter to send, Shift+Enter for new line</span>
        ) : (
          <span>Press Shift+Enter to send</span>
        )}
      </div>
    </form>
  );
};