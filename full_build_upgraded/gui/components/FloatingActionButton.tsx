import React from 'react';
import { Plus, Zap, Settings, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FABProps {
  onClick?: () => void;
  icon?: 'plus' | 'zap' | 'settings' | 'help';
  label?: string;
  className?: string;
}

const icons = {
  plus: Plus,
  zap: Zap,
  settings: Settings,
  help: HelpCircle,
};

export function FloatingActionButton({ 
  onClick, 
  icon = 'plus',
  label,
  className 
}: FABProps) {
  const Icon = icons[icon];

  return (
    <button
      onClick={onClick}
      className={cn(
        'group fixed bottom-6 right-6 z-50',
        'w-16 h-16 rounded-full',
        'bg-gradient-to-r from-primary-600 to-accent-600',
        'shadow-neon-mixed hover:shadow-glow-lg',
        'flex items-center justify-center',
        'transition-all duration-300',
        'hover:scale-110 hover:rotate-90',
        'active:scale-95',
        'ripple-effect',
        className
      )}
      aria-label={label || 'Action'}
    >
      <Icon className="h-7 w-7 text-white transition-transform duration-300 group-hover:scale-110" />
      
      {/* Tooltip */}
      {label && (
        <span className="absolute right-20 px-4 py-2 bg-gray-900 dark:bg-gray-800 text-white text-sm rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
          {label}
        </span>
      )}
    </button>
  );
}

interface FABMenuProps {
  actions: Array<{
    icon: 'plus' | 'zap' | 'settings' | 'help';
    label: string;
    onClick: () => void;
  }>;
  mainIcon?: 'plus' | 'zap' | 'settings' | 'help';
}

export function FloatingActionMenu({ actions, mainIcon = 'plus' }: FABMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const MainIcon = icons[mainIcon];

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col-reverse items-end gap-4">
      {/* Sub actions */}
      <div className={cn(
        'flex flex-col-reverse gap-3 transition-all duration-300',
        isOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
      )}>
        {actions.map((action, index) => {
          const Icon = icons[action.icon];
          return (
            <button
              key={index}
              onClick={() => {
                action.onClick();
                setIsOpen(false);
              }}
              className="group flex items-center gap-3 animate-fade-in-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <span className="px-4 py-2 bg-gray-900 dark:bg-gray-800 text-white text-sm rounded-lg whitespace-nowrap shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                {action.label}
              </span>
              <div className="w-14 h-14 rounded-full bg-gradient-to-r from-primary-500 to-accent-500 shadow-neon-mixed hover:shadow-glow-lg flex items-center justify-center transition-all duration-300 hover:scale-110">
                <Icon className="h-6 w-6 text-white" />
              </div>
            </button>
          );
        })}
      </div>

      {/* Main button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-16 h-16 rounded-full',
          'bg-gradient-to-r from-primary-600 to-accent-600',
          'shadow-neon-mixed hover:shadow-glow-lg',
          'flex items-center justify-center',
          'transition-all duration-300',
          'hover:scale-110',
          'active:scale-95',
          isOpen && 'rotate-45'
        )}
      >
        <MainIcon className="h-7 w-7 text-white" />
      </button>
    </div>
  );
}
