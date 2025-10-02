
import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { useEffect } from 'react';
import { apiClient } from '@/lib/api';

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Load auth token on app start
    apiClient.loadToken();
  }, []);

  return <Component {...pageProps} />;
}
