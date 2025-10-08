import React, { useEffect, useState, useCallback } from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

const icons = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
};

const bgColors = {
  success: 'bg-gradient-to-r from-emerald-500 to-green-600',
  error: 'bg-gradient-to-r from-rose-500 to-red-600',
  info: 'bg-gradient-to-r from-blue-500 to-indigo-600',
};

export function Toast({ id, type, message, duration = 5000, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  const Icon = icons[type];

  const handleClose = useCallback(() => {
    setIsLeaving(true);
    setTimeout(() => onClose(id), 300);
  }, [id, onClose]);

  useEffect(() => {
    // Trigger animation
    requestAnimationFrame(() => setIsVisible(true));

    // Auto dismiss
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, handleClose]);

  return (
    <div
      className={cn(
        'min-w-[320px] max-w-md rounded-2xl shadow-2xl px-5 py-4 flex items-start gap-3 transition-all duration-300',
        bgColors[type],
        isVisible && !isLeaving ? 'translate-x-0 opacity-100' : 'translate-x-[400px] opacity-0',
        'backdrop-blur-xl border border-white/20'
      )}
    >
      <Icon className="h-6 w-6 text-white flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-white font-medium leading-relaxed">{message}</p>
      </div>
      <button
        onClick={handleClose}
        className="flex-shrink-0 p-1 rounded-lg hover:bg-white/20 transition-colors"
      >
        <X className="h-4 w-4 text-white" />
      </button>
    </div>
  );
}

export interface ToastContainerProps {
  toasts: ToastProps[];
  onClose: (id: string) => void;
}

export function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-[10000] space-y-3">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onClose={onClose} />
      ))}
    </div>
  );
}

// Hook for using toasts
export function useToast() {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const addToast = (type: 'success' | 'error' | 'info', message: string, duration?: number) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { id, type, message, duration, onClose: removeToast }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const success = (message: string, duration?: number) => addToast('success', message, duration);
  const error = (message: string, duration?: number) => addToast('error', message, duration);
  const info = (message: string, duration?: number) => addToast('info', message, duration);

  return {
    toasts,
    success,
    error,
    info,
    removeToast,
    ToastContainer: () => <ToastContainer toasts={toasts} onClose={removeToast} />,
  };
}
