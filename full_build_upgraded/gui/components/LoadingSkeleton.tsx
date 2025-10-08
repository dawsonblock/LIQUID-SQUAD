import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'wave',
}: SkeletonProps) {
  const baseStyles = 'bg-gray-200 dark:bg-gray-700';
  
  const variantStyles = {
    text: 'rounded-md h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-xl',
  };

  const animationStyles = {
    pulse: 'animate-pulse',
    wave: 'skeleton',
    none: '',
  };

  return (
    <div
      className={cn(
        baseStyles,
        variantStyles[variant],
        animationStyles[animation],
        className
      )}
      style={{
        width: width ? (typeof width === 'number' ? `${width}px` : width) : undefined,
        height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined,
      }}
    />
  );
}

export function ChatMessageSkeleton() {
  return (
    <div className="flex animate-fade-in-up">
      <div className="max-w-3xl w-full">
        <div className="glass-effect rounded-2xl px-5 py-4 border border-gray-200/50 dark:border-gray-700/50">
          {/* Iterations */}
          <div className="mb-6">
            <div className="flex items-center space-x-2 mb-4">
              <Skeleton variant="circular" width={8} height={8} />
              <Skeleton variant="text" width={120} height={16} />
            </div>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass-effect rounded-xl p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="text" width={80} height={16} />
                    <Skeleton variant="rounded" width={60} height={20} className="ml-auto" />
                  </div>
                  <Skeleton variant="text" width="100%" height={12} className="mb-2" />
                  <Skeleton variant="text" width="85%" height={12} />
                </div>
              ))}
            </div>
          </div>

          {/* Answer */}
          <div className="space-y-3">
            <Skeleton variant="text" width="100%" height={12} />
            <Skeleton variant="text" width="95%" height={12} />
            <Skeleton variant="text" width="88%" height={12} />
            <Skeleton variant="text" width="92%" height={12} />
          </div>

          {/* Metadata */}
          <div className="mt-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
            <div className="flex flex-wrap items-center gap-2">
              <Skeleton variant="rounded" width={60} height={24} />
              <Skeleton variant="rounded" width={80} height={24} />
              <Skeleton variant="rounded" width={100} height={24} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SidebarSkeleton() {
  return (
    <div className="p-4 space-y-4 animate-fade-in">
      {/* Navigation */}
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-3">
            <Skeleton variant="circular" width={20} height={20} />
            <Skeleton variant="text" width={100} height={16} />
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="space-y-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
        {[1, 2, 3].map((i) => (
          <div key={i}>
            <Skeleton variant="text" width={80} height={14} className="mb-2" />
            <Skeleton variant="rounded" width="100%" height={40} />
          </div>
        ))}
      </div>
    </div>
  );
}

export function MetricsCardSkeleton() {
  return (
    <div className="glass-effect rounded-2xl p-6 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <Skeleton variant="text" width={120} height={20} />
        <Skeleton variant="circular" width={32} height={32} />
      </div>
      <Skeleton variant="text" width={80} height={32} className="mb-2" />
      <Skeleton variant="text" width={150} height={12} />
      <div className="mt-6">
        <Skeleton variant="rounded" width="100%" height={200} />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="glass-effect rounded-2xl overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} variant="text" width={i === 0 ? 200 : 120} height={16} />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex items-center gap-4 px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50 last:border-b-0"
        >
          {Array.from({ length: cols }).map((_, colIndex) => (
            <Skeleton key={colIndex} variant="text" width={colIndex === 0 ? 200 : 120} height={16} />
          ))}
        </div>
      ))}
    </div>
  );
}
