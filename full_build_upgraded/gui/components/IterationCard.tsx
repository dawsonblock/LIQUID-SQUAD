import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, CheckCircle, RefreshCw } from 'lucide-react';
import { SelfLoopIteration } from '@/lib/api';
import { cn, formatTimestamp } from '@/lib/utils';

interface IterationCardProps {
  iteration: SelfLoopIteration;
  index: number;
}

const stepIcons = {
  plan: '📋',
  draft: '✏️',
  critic: '🔍',
  verify: '✅',
  revise: '🔄',
};

const stepColors = {
  plan: 'from-blue-500/10 to-cyan-500/10 border-blue-300/50 dark:border-blue-700/50',
  draft: 'from-green-500/10 to-emerald-500/10 border-green-300/50 dark:border-green-700/50',
  critic: 'from-yellow-500/10 to-amber-500/10 border-yellow-300/50 dark:border-yellow-700/50',
  verify: 'from-purple-500/10 to-pink-500/10 border-purple-300/50 dark:border-purple-700/50',
  revise: 'from-orange-500/10 to-red-500/10 border-orange-300/50 dark:border-orange-700/50',
};

const stepGradients = {
  plan: 'from-blue-600 to-cyan-600',
  draft: 'from-green-600 to-emerald-600',
  critic: 'from-yellow-600 to-amber-600',
  verify: 'from-purple-600 to-pink-600',
  revise: 'from-orange-600 to-red-600',
};

export default function IterationCard({ iteration, index }: IterationCardProps) {
  const [isExpanded, setIsExpanded] = useState(index === 0); // First iteration expanded by default

  const stepName = iteration.step.charAt(0).toUpperCase() + iteration.step.slice(1);
  const icon = stepIcons[iteration.step] || '⚡';
  const colorClass = stepColors[iteration.step] || 'from-gray-500/10 to-gray-500/10 border-gray-300/50 dark:border-gray-700/50';
  const gradientClass = stepGradients[iteration.step] || 'from-gray-600 to-gray-600';

  return (
    <div className={cn('rounded-xl border-2 bg-gradient-to-r transition-all duration-300 hover:shadow-lg animate-slide-up', colorClass)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-white/50 dark:hover:bg-black/20 rounded-xl transition-all duration-200 group"
      >
        <div className="flex items-center space-x-4 flex-1">
          <div className="relative">
            <div className={cn('absolute inset-0 bg-gradient-to-r rounded-full blur-md opacity-30 group-hover:opacity-50 transition-opacity', gradientClass)}></div>
            <span className="relative text-2xl">{icon}</span>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={cn('font-bold text-base bg-gradient-to-r bg-clip-text text-transparent', gradientClass)}>
              Step {index + 1}: {stepName}
            </h3>
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-1.5 text-xs text-gray-600 dark:text-gray-400">
              <span className="flex items-center space-x-1 px-2 py-0.5 bg-white/60 dark:bg-gray-800/60 rounded-md">
                <RefreshCw className="h-3 w-3" />
                <span className="font-medium">Round {iteration.round}</span>
              </span>
              <span className="flex items-center space-x-1 px-2 py-0.5 bg-white/60 dark:bg-gray-800/60 rounded-md">
                <Clock className="h-3 w-3" />
                <span>{formatTimestamp(iteration.timestamp)}</span>
              </span>
              {iteration.confidence && (
                <span className={cn(
                  'flex items-center space-x-1 px-2 py-0.5 rounded-md font-semibold',
                  iteration.confidence > 0.8 
                    ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
                    : iteration.confidence > 0.6
                    ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300'
                    : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
                )}>
                  <span>{(iteration.confidence * 100).toFixed(0)}%</span>
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-3 ml-3">
          {iteration.confidence && iteration.confidence > 0.8 && (
            <CheckCircle className="h-5 w-5 text-green-500 animate-pulse" />
          )}
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-5 pb-4 border-t border-gray-200/50 dark:border-gray-700/50 animate-slide-down">
          <div className="mt-4 prose prose-sm dark:prose-invert max-w-none">
            <div className="bg-white/60 dark:bg-gray-900/60 rounded-xl p-4 backdrop-blur-sm">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-transparent p-0 border-0 m-0 font-mono leading-relaxed">
                {iteration.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
