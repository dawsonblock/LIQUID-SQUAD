import React from 'react';
import { Sparkles, Code, BookOpen, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

const prompts = [
  {
    icon: <Code size={18} />,
    text: 'Help me debug this code',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: <BookOpen size={18} />,
    text: 'Explain a complex concept',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: <Lightbulb size={18} />,
    text: 'Give me creative ideas',
    color: 'from-yellow-500 to-orange-500',
  },
  {
    icon: <Sparkles size={18} />,
    text: 'Write a technical document',
    color: 'from-green-500 to-teal-500',
  },
];

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({ onSelectPrompt }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl mx-auto animate-fade-in">
      {prompts.map((prompt, index) => (
        <button
          key={index}
          onClick={() => onSelectPrompt(prompt.text)}
          className="group relative overflow-hidden p-4 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-transparent hover:shadow-lg transition-all text-left"
          data-testid={`suggested-prompt-${index}`}
        >
          <div className={cn(
            'absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity',
            prompt.color
          )} />
          <div className="relative flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-xl bg-gradient-to-br text-white',
              prompt.color
            )}>
              {prompt.icon}
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">
              {prompt.text}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
};