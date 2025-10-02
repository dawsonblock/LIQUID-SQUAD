import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  MessageSquare,
  BarChart3,
  Settings,
  Menu,
  X,
  Bot,
  Database,
  Shield,
  ExternalLink,
  Moon,
  Sun,
} from 'lucide-react';
import { cn, toggleDarkMode, isDarkMode, getStoredAuthToken, setStoredAuthToken } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  modelTier: string;
  onModelTierChange: (tier: string) => void;
  retrievalMode: string;
  onRetrievalModeChange: (mode: string) => void;
  criticEnabled: boolean;
  onCriticToggle: (enabled: boolean) => void;
}

const navigation = [
  { name: 'Chat', href: '/', icon: MessageSquare },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

const modelTiers = [
  { value: 'auto', label: 'Auto' },
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large' },
];

const retrievalModes = [
  { value: 'disabled', label: 'Disabled' },
  { value: 'dense', label: 'Dense' },
  { value: 'sparse', label: 'Sparse' },
  { value: 'dual', label: 'Dual' },
];

export default function Sidebar({
  isOpen,
  onToggle,
  modelTier,
  onModelTierChange,
  retrievalMode,
  onRetrievalModeChange,
  criticEnabled,
  onCriticToggle,
}: SidebarProps) {
  const router = useRouter();
  const [authToken, setAuthToken] = useState('');
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const token = getStoredAuthToken();
    if (token) {
      setAuthToken(token);
    }
    setDarkMode(isDarkMode());
  }, []);

  const handleAuthTokenChange = (token: string) => {
    setAuthToken(token);
    setStoredAuthToken(token);
  };

  const handleDarkModeToggle = () => {
    toggleDarkMode();
    setDarkMode(!darkMode);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-80 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <Bot className="h-8 w-8 text-primary-600" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                LIQUID-SQUAD
              </h1>
            </div>
            <button
              onClick={onToggle}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = router.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'sidebar-item',
                    isActive ? 'sidebar-item-active' : 'sidebar-item-inactive'
                  )}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Controls */}
          <div className="px-4 py-6 border-t border-gray-200 dark:border-gray-700 space-y-6">
            {/* Auth Token */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Shield className="inline h-4 w-4 mr-1" />
                Auth Token
              </label>
              <input
                type="password"
                value={authToken}
                onChange={(e) => handleAuthTokenChange(e.target.value)}
                placeholder="Enter auth token..."
                className="input-field text-xs"
              />
            </div>

            {/* Model Tier */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Bot className="inline h-4 w-4 mr-1" />
                Model Tier
              </label>
              <select
                value={modelTier}
                onChange={(e) => onModelTierChange(e.target.value)}
                className="input-field text-sm"
              >
                {modelTiers.map((tier) => (
                  <option key={tier.value} value={tier.value}>
                    {tier.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Retrieval Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Database className="inline h-4 w-4 mr-1" />
                Retrieval Mode
              </label>
              <select
                value={retrievalMode}
                onChange={(e) => onRetrievalModeChange(e.target.value)}
                className="input-field text-sm"
              >
                {retrievalModes.map((mode) => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Critic Toggle */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={criticEnabled}
                  onChange={(e) => onCriticToggle(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable Critic
                </span>
              </label>
            </div>

            {/* Dark Mode Toggle */}
            <div>
              <button
                onClick={handleDarkModeToggle}
                className="flex items-center w-full p-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {darkMode ? (
                  <Sun className="h-4 w-4 mr-2" />
                ) : (
                  <Moon className="h-4 w-4 mr-2" />
                )}
                {darkMode ? 'Light Mode' : 'Dark Mode'}
              </button>
            </div>

            {/* Documentation Link */}
            <div>
              <a
                href="https://github.com/your-repo/liquid-squad"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center w-full p-2 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Documentation
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}