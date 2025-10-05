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
          'fixed inset-y-0 left-0 z-50 w-80 glass-effect shadow-2xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-gray-200/50 dark:border-gray-700/50 bg-gradient-to-r from-primary-500/5 to-accent-500/5">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="absolute inset-0 bg-primary-500/20 rounded-full blur-md animate-pulse-slow"></div>
                <Bot className="relative h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold gradient-text">
                  LIQUID-SQUAD
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">AI Agent System</p>
              </div>
            </div>
            <button
              onClick={onToggle}
              className="lg:hidden p-2 rounded-xl text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-gray-700 transition-all duration-200"
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
          <div className="px-4 py-6 border-t border-gray-200/50 dark:border-gray-700/50 space-y-5 bg-gradient-to-b from-transparent to-primary-500/5">
            {/* Auth Token */}
            <div className="group">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2.5 flex items-center">
                <div className="p-1.5 bg-primary-100 dark:bg-primary-900/30 rounded-lg mr-2">
                  <Shield className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
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
            <div className="group">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2.5 flex items-center">
                <div className="p-1.5 bg-accent-100 dark:bg-accent-900/30 rounded-lg mr-2">
                  <Bot className="h-4 w-4 text-accent-600 dark:text-accent-400" />
                </div>
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
            <div className="group">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2.5 flex items-center">
                <div className="p-1.5 bg-primary-100 dark:bg-primary-900/30 rounded-lg mr-2">
                  <Database className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                </div>
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
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-accent-50 to-primary-50 dark:from-accent-900/20 dark:to-primary-900/20 rounded-xl border border-accent-200/30 dark:border-accent-700/30">
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                Enable Critic
              </span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={criticEnabled}
                  onChange={(e) => onCriticToggle(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
              </label>
            </div>

            {/* Dark Mode Toggle */}
            <div>
              <button
                onClick={handleDarkModeToggle}
                className="flex items-center justify-between w-full p-3 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gradient-to-r hover:from-primary-50 hover:to-accent-50 dark:hover:from-gray-700 dark:hover:to-gray-600 transition-all duration-200 group"
              >
                <div className="flex items-center">
                  {darkMode ? (
                    <Sun className="h-5 w-5 mr-3 text-amber-500" />
                  ) : (
                    <Moon className="h-5 w-5 mr-3 text-indigo-500" />
                  )}
                  <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                  {darkMode ? '☀️' : '🌙'}
                </div>
              </button>
            </div>

            {/* Documentation Link */}
            <div>
              <a
                href="https://github.com/your-repo/liquid-squad"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between w-full p-3 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gradient-to-r hover:from-primary-50 hover:to-accent-50 dark:hover:from-gray-700 dark:hover:to-gray-600 transition-all duration-200 group"
              >
                <div className="flex items-center">
                  <ExternalLink className="h-5 w-5 mr-3 text-primary-600 dark:text-primary-400" />
                  <span>Documentation</span>
                </div>
                <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xs">→</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}