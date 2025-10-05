import React, { useEffect, useState } from 'react';
import { useChatStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Search, MessageSquare, Settings, Moon, Sun, Trash2, Download } from 'lucide-react';

interface Command {
  id: string;
  label: string;
  icon: React.ReactNode;
  action: () => void;
  group: string;
}

export const CommandPalette: React.FC = () => {
  const { uiState, toggleCommandPalette, createConversation, toggleSettings, deleteConversation, conversations } = useChatStore();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const commands: Command[] = [
    {
      id: 'new-chat',
      label: 'New Chat',
      icon: <MessageSquare size={18} />,
      action: () => {
        createConversation();
        toggleCommandPalette();
      },
      group: 'Actions',
    },
    {
      id: 'settings',
      label: 'Open Settings',
      icon: <Settings size={18} />,
      action: () => {
        toggleSettings();
        toggleCommandPalette();
      },
      group: 'Actions',
    },
    {
      id: 'delete-all',
      label: 'Delete All Conversations',
      icon: <Trash2 size={18} />,
      action: () => {
        if (confirm('Are you sure you want to delete all conversations?')) {
          conversations.forEach((conv) => deleteConversation(conv.id));
        }
        toggleCommandPalette();
      },
      group: 'Danger',
    },
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  const commandsRef = React.useRef<Command[]>(filteredCommands);
  const selectedIndexRef = React.useRef<number>(selectedIndex);
  const isOpenRef = React.useRef<boolean>(uiState.isCommandPaletteOpen);

  useEffect(() => { commandsRef.current = filteredCommands; }, [filteredCommands]);
  useEffect(() => { selectedIndexRef.current = selectedIndex; }, [selectedIndex]);
  useEffect(() => { isOpenRef.current = uiState.isCommandPaletteOpen; }, [uiState.isCommandPaletteOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        toggleCommandPalette();
        return;
      }
      if (!isOpenRef.current) return;

      if (e.key === 'Escape') {
        toggleCommandPalette();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, commandsRef.current.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const cmd = commandsRef.current[selectedIndexRef.current];
        cmd?.action();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleCommandPalette]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  if (!uiState.isCommandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={toggleCommandPalette}
      data-testid="command-palette-overlay"
    >
      <div
        className="w-full max-w-2xl glass rounded-xl shadow-2xl overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
          <Search size={20} className="text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent outline-none text-gray-900 dark:text-gray-100"
            autoFocus
            data-testid="command-palette-input"
          />
          <kbd className="px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 dark:bg-gray-800 rounded">
            ESC
          </kbd>
        </div>

        <div className="max-h-96 overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No commands found</div>
          ) : (
            <div className="space-y-1">
              {filteredCommands.map((command, index) => (
                <button
                  key={command.id}
                  onClick={command.action}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors',
                    index === selectedIndex
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-900 dark:text-primary-100'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300',
                    command.group === 'Danger' && 'text-red-600 dark:text-red-400'
                  )}
                  data-testid={`command-${command.id}`}
                >
                  {command.icon}
                  <span className="flex-1">{command.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500">
          <span>Press ↑↓ to navigate</span>
          <span>Press ↵ to select</span>
        </div>
      </div>
    </div>
  );
};