import React, { useEffect, useState, useRef } from 'react';
import { Search, Command, ArrowRight, Sparkles, Settings, MessageSquare, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  icon: 'message' | 'settings' | 'chart' | 'sparkles';
  action: () => void;
  shortcut?: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
}

const icons = {
  message: MessageSquare,
  settings: Settings,
  chart: BarChart3,
  sparkles: Sparkles,
};

export function CommandPalette({ isOpen, onClose, commands }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredCommands = commands.filter((cmd) =>
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    (cmd.subtitle && cmd.subtitle.toLowerCase().includes(query.toLowerCase()))
  );

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        e.preventDefault();
        filteredCommands[selectedIndex].action();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9998] animate-fade-in"
        onClick={onClose}
      />

      {/* Command Palette */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl z-[9999] px-4 animate-scale-in">
        <div className="glass-effect rounded-2xl shadow-2xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <Search className="h-5 w-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">
                ESC
              </kbd>
            </div>
          </div>

          {/* Commands List */}
          <div className="max-h-96 overflow-y-auto scrollbar-thin">
            {filteredCommands.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <Sparkles className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">No commands found</p>
              </div>
            ) : (
              <div className="py-2">
                {filteredCommands.map((cmd, index) => {
                  const Icon = icons[cmd.icon];
                  const isSelected = index === selectedIndex;

                  return (
                    <button
                      key={cmd.id}
                      onClick={() => {
                        cmd.action();
                        onClose();
                      }}
                      className={cn(
                        'w-full flex items-center gap-4 px-6 py-3 transition-all duration-200',
                        isSelected
                          ? 'bg-gradient-to-r from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 border-l-4 border-primary-500'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                      )}
                    >
                      <div className={cn(
                        'p-2 rounded-lg transition-all duration-200',
                        isSelected
                          ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      )}>
                        <Icon className="h-5 w-5" />
                      </div>

                      <div className="flex-1 text-left">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {cmd.title}
                        </div>
                        {cmd.subtitle && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {cmd.subtitle}
                          </div>
                        )}
                      </div>

                      {cmd.shortcut && (
                        <kbd className="hidden sm:block px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600 text-xs text-gray-600 dark:text-gray-400">
                          {cmd.shortcut}
                        </kbd>
                      )}

                      {isSelected && (
                        <ArrowRight className="h-4 w-4 text-primary-500" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200/50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <Command className="h-3.5 w-3.5" />
              <span>Command Palette</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">↵</kbd>
                Select
              </span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Hook for using command palette
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen((prev) => !prev),
  };
}
