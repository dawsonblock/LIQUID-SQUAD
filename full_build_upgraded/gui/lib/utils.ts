import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    return `${(ms / 60000).toFixed(1)}m`;
  }
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function getStoredAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('liquid-squad-auth-token');
}

export function setStoredAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('liquid-squad-auth-token', token);
}

export function removeStoredAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('liquid-squad-auth-token');
}

export function getStoredSettings(): Record<string, any> {
  if (typeof window === 'undefined') return {};
  try {
    const settings = localStorage.getItem('liquid-squad-settings');
    return settings ? JSON.parse(settings) : {};
  } catch {
    return {};
  }
}

export function setStoredSettings(settings: Record<string, any>): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('liquid-squad-settings', JSON.stringify(settings));
}

export function isDarkMode(): boolean {
  if (typeof window === 'undefined') return false;
  return document.documentElement.classList.contains('dark');
}

export function toggleDarkMode(): void {
  if (typeof window === 'undefined') return;
  document.documentElement.classList.toggle('dark');
  const isDark = document.documentElement.classList.contains('dark');
  localStorage.setItem('liquid-squad-theme', isDark ? 'dark' : 'light');
}

export function initializeDarkMode(): void {
  if (typeof window === 'undefined') return;
  
  const stored = localStorage.getItem('liquid-squad-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (stored === 'dark' || (!stored && prefersDark)) {
    document.documentElement.classList.add('dark');
  }
}