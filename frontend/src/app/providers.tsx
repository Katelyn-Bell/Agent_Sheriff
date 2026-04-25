"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useAppStream } from "@/lib/ws";

function StreamSubscriber({ children }: { children: React.ReactNode }) {
  useAppStream();
  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
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
    <QueryClientProvider client={client}>
      <StreamSubscriber>{children}</StreamSubscriber>
    </QueryClientProvider>
  );
}
