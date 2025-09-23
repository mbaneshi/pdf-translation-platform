import React from 'react';
import type { AppProps } from 'next/app';
import '../styles/globals.css';
import { ThemeProvider } from '../contexts/ThemeContext';
import { AuthProvider } from '../contexts/AuthContext';
import { GlossaryProvider } from '../contexts/GlossaryContext';
import { TranslationProvider } from '../contexts/TranslationContext';
import AppLayout from '../components/Layout/AppLayout';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentProvider } from '../contexts/DocumentContext';

export default function App({ Component, pageProps }: AppProps) {
  const [client] = React.useState(() => new QueryClient());
  return (
    <ThemeProvider>
      <QueryClientProvider client={client}>
        <AuthProvider>
          <GlossaryProvider>
            <TranslationProvider>
              <DocumentProvider>
                <AppLayout>
                  <Component {...pageProps} />
                </AppLayout>
              </DocumentProvider>
            </TranslationProvider>
          </GlossaryProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
