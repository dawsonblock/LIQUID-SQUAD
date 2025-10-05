import React from 'react';
import { useChatStore } from '@/lib/store';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';
import { X, Sun, Moon, Monitor, Type, Code } from 'lucide-react';

export const SettingsPanel: React.FC = () => {
  const { uiState, toggleSettings, settings, updateSettings } = useChatStore();
  const { theme, setTheme } = useTheme();

  if (!uiState.isSettingsOpen) return null;

  const themeOptions = [
    { value: 'light', label: 'Light', icon: <Sun size={18} /> },
    { value: 'dark', label: 'Dark', icon: <Moon size={18} /> },
    { value: 'system', label: 'System', icon: <Monitor size={18} /> },
  ];

  const fontSizeOptions = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium' },
    { value: 'large', label: 'Large' },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={toggleSettings}
      data-testid="settings-panel-overlay"
    >
      <div
        className="w-full max-w-2xl glass rounded-2xl shadow-2xl overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
          <button
            onClick={toggleSettings}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            data-testid="close-settings-button"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Theme Selection */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Theme
            </label>
            <div className="grid grid-cols-3 gap-3">
              {themeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTheme(option.value as any)}
                  className={cn(
                    'flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all',
                    theme === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  )}
                  data-testid={`theme-option-${option.value}`}
                >
                  <div className={cn(
                    'text-gray-600 dark:text-gray-400',
                    theme === option.value && 'text-primary-600 dark:text-primary-400'
                  )}>
                    {option.icon}
                  </div>
                  <span className={cn(
                    'text-sm font-medium text-gray-700 dark:text-gray-300',
                    theme === option.value && 'text-primary-600 dark:text-primary-400'
                  )}>
                    {option.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Font Size */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              <Type size={18} className="inline mr-2" />
              Font Size
            </label>
            <div className="grid grid-cols-3 gap-3">
              {fontSizeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => updateSettings({ fontSize: option.value as any })}
                  className={cn(
                    'p-3 rounded-xl border-2 transition-all text-center',
                    settings.fontSize === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  )}
                  data-testid={`font-size-${option.value}`}
                >
                  <span className="text-sm font-medium">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Code Theme */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              <Code size={18} className="inline mr-2" />
              Code Block Theme
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => updateSettings({ codeTheme: 'dark' })}
                className={cn(
                  'p-3 rounded-xl border-2 transition-all',
                  settings.codeTheme === 'dark'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                )}
                data-testid="code-theme-dark"
              >
                <span className="text-sm font-medium">Dark</span>
              </button>
              <button
                onClick={() => updateSettings({ codeTheme: 'light' })}
                className={cn(
                  'p-3 rounded-xl border-2 transition-all',
                  settings.codeTheme === 'light'
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                )}
                data-testid="code-theme-light"
              >
                <span className="text-sm font-medium">Light</span>
              </button>
            </div>
          </div>

          {/* Toggles */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Send on Enter</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Use Shift+Enter for new line
                </p>
              </div>
              <button
                onClick={() => updateSettings({ sendOnEnter: !settings.sendOnEnter })}
                className={cn(
                  'relative w-14 h-7 rounded-full transition-colors',
                  settings.sendOnEnter ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                )}
                data-testid="send-on-enter-toggle"
              >
                <div
                  className={cn(
                    'absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white transition-transform',
                    settings.sendOnEnter && 'translate-x-7'
                  )}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Show Timestamps</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Display message timestamps
                </p>
              </div>
              <button
                onClick={() => updateSettings({ showTimestamps: !settings.showTimestamps })}
                className={cn(
                  'relative w-14 h-7 rounded-full transition-colors',
                  settings.showTimestamps ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                )}
                data-testid="show-timestamps-toggle"
              >
                <div
                  className={cn(
                    'absolute top-0.5 left-0.5 w-6 h-6 rounded-full bg-white transition-transform',
                    settings.showTimestamps && 'translate-x-7'
                  )}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            LIQUID HIVE 25 - Advanced Multi-Tier LLM System
          </p>
        </div>
      </div>
    </div>
  );
};