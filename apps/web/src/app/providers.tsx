'use client';

import { useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommandPalette } from '@/components/command-palette';

/**
 * Client-side providers: TanStack Query for server/graph state and the
 * always-mounted ⌘K command palette. Local-first + optimistic UI live here.
 */
export function Providers({ children }: { children: ReactNode }) {
  // One QueryClient per app instance; created lazily so it survives re-renders.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <CommandPalette />
    </QueryClientProvider>
  );
}
