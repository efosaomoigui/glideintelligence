"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * 🛰️ TopicAutoRefresher
 * 
 * Silently refreshes the page's Server Components (Hero, Pulse, etc.) 
 * whenever new intelligence is likely to be ready.
 * 
 * Place this in your main layout or specifically in the Hero section.
 */
export default function TopicAutoRefresher({ intervalMs = 30000 }) {
  const router = useRouter();

  useEffect(() => {
    const interval = setInterval(() => {
      // router.refresh() re-validates server components on the current page.
      // It updates the UI with new data from the backend without a full page reload
      // or losing user state (carousel position, scroll, etc).
      router.refresh();
      console.log("TopicAutoRefresher: Silently refreshing data...");
    }, intervalMs);

    return () => clearInterval(interval);
  }, [router, intervalMs]);

  return null; // Invisible utility component
}
