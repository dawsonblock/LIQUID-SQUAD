import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, Clock, CheckCircle } from 'lucide-react';
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
  plan: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
  draft: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
  critic: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
  verify: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
  revise: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
};

export default function IterationCard({ iteration, index }: IterationCardProps) {
  const [isExpanded, setIsExpanded] = useState(index === 0); // First iteration expanded by default

  const stepName = iteration.step.charAt(0).toUpperCase() + iteration.step.slice(1);
  const icon = stepIcons[iteration.step] || '⚡';
  const colorClass = stepColors[iteration.step] || 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';

  return (
    <div className={cn('rounded-lg border-2 transition-all duration-200', colorClass)}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-black/5 dark:hover:bg-white/5 rounded-t-lg transition-colors"
      >
        <div className="flex items-center space-x-3">
          <span className="text-lg">{icon}</span>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">
              Step {index + 1}: {stepName}
            </h3>
            <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
              <Clock className="h-3 w-3" />
              <span>{formatTimestamp(iteration.timestamp)}</span>
              {iteration.confidence && (
                <>
                  <span>•</span>
                  <span>Confidence: {(iteration.confidence * 100).toFixed(1)}%</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {iteration.confidence && iteration.confidence > 0.8 && (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-black/10 dark:border-white/10">
          <div className="mt-3 prose prose-sm dark:prose-invert max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300 bg-transparent p-0 border-0">
              {iteration.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}