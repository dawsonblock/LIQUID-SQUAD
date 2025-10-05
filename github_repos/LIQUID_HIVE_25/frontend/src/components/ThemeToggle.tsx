import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
        isDark ? 'bg-gray-700' : 'bg-primary-200'
      )}
      aria-label="Toggle theme"
      data-testid="theme-toggle-button"
    >
      <div
        className={cn(
          'absolute top-0.5 left-0.5 w-6 h-6 rounded-full transition-transform duration-300 flex items-center justify-center',
          isDark ? 'translate-x-7 bg-gray-900' : 'translate-x-0 bg-white'
        )}
      >
        {isDark ? (
          <Moon size={14} className="text-yellow-300" />
        ) : (
          <Sun size={14} className="text-yellow-500" />
        )}
      </div>
    </button>
  );
};