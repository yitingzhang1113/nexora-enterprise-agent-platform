"use client";

import { AppSidebar } from "@/components/sidebar/AppSidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg-0 text-text-5">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
