import React, { useState } from 'react';
import { Plus, MessageSquare, Trash2, Settings, Search, Sparkles, ChevronLeft, Menu } from 'lucide-react';
import { Conversation } from '@/lib/store';
import { cn, formatTimestamp, truncateText } from '@/lib/utils';
import { useChatStore } from '@/lib/store';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  currentConversationId,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}) => {
  const { uiState, setSearchQuery, toggleSettings, toggleSidebar } = useChatStore();
  const [localSearch, setLocalSearch] = useState('');

  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(localSearch.toLowerCase())
  );

  const handleSearchChange = (value: string) => {
    setLocalSearch(value);
    setSearchQuery(value);
  };

  if (!uiState.isSidebarOpen) {
    return (
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-40 p-3 rounded-xl glass shadow-lg hover:shadow-xl transition-all"
        data-testid="open-sidebar-button"
      >
        <Menu size={24} className="text-gray-700 dark:text-gray-300" />
      </button>
    );
  }

  return (
    <div className="w-80 h-full glass border-r border-gray-200 dark:border-gray-700 flex flex-col shadow-xl animate-slide-in" data-testid="sidebar">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <h1 className="text-lg font-bold gradient-text">LIQUID HIVE</h1>
          </div>
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            data-testid="close-sidebar-button"
          >
            <ChevronLeft size={20} />
          </button>
        </div>
        
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700 text-white rounded-xl transition-all shadow-md hover:shadow-lg"
          data-testid="new-chat-button"
        >
          <Plus size={20} />
          <span className="font-medium">New Chat</span>
        </button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="relative">
          <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all text-sm"
            data-testid="search-conversations-input"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2">
        {filteredConversations.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-8 px-4">
            <MessageSquare size={48} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">
              {localSearch ? 'No conversations found' : 'No conversations yet'}
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredConversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  'group relative p-3 rounded-xl cursor-pointer transition-all',
                  currentConversationId === conv.id
                    ? 'bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 shadow-sm'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800/50'
                )}
                onClick={() => onSelectConversation(conv.id)}
                data-testid={`conversation-${conv.id}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className={cn(
                      'text-sm font-medium truncate',
                      currentConversationId === conv.id
                        ? 'text-primary-900 dark:text-primary-100'
                        : 'text-gray-700 dark:text-gray-300'
                    )}>
                      {truncateText(conv.title, 35)}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatTimestamp(conv.updatedAt)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this conversation?')) {
                        const isCurrent = currentConversationId === conv.id;
                        onDeleteConversation(conv.id);
                        if (isCurrent) {
                          const nextConv = conversations.find(c => c.id !== conv.id);
                          onSelectConversation(nextConv?.id || null);
                        }
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg transition-all"
                    title="Delete conversation"
                    data-testid={`delete-conversation-${conv.id}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={toggleSettings}
          className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors text-gray-700 dark:text-gray-300"
          data-testid="settings-button"
        >
          <Settings size={20} />
          <span className="font-medium">Settings</span>
        </button>
      </div>
    </div>
  );
};