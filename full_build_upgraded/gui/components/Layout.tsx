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
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
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
        <div className="lg:hidden bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              LIQUID-SQUAD
            </h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}