import React, { ReactNode } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
  modelTier: string;
  onModelTierChange: (tier: string) => void;
  retrievalMode: string;
  onRetrievalModeChange: (mode: string) => void;
  criticEnabled: boolean;
  onCriticToggle: (enabled: boolean) => void;
}

export default function Layout({
  children,
  modelTier,
  onModelTierChange,
  retrievalMode,
  onRetrievalModeChange,
  criticEnabled,
  onCriticToggle,
}: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-primary-50/30 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        modelTier={modelTier}
        onModelTierChange={onModelTierChange}
        retrievalMode={retrievalMode}
        onRetrievalModeChange={onRetrievalModeChange}
        criticEnabled={criticEnabled}
        onCriticToggle={onCriticToggle}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden lg:ml-0">
        {/* Mobile header */}
        <div className="lg:hidden glass-effect shadow-lg border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between px-4 py-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-xl text-gray-500 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-gray-700 transition-all duration-200"
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="text-lg font-bold gradient-text">
              LIQUID-SQUAD
            </h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
}