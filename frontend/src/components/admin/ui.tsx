"use client";

import { cn } from "@/lib/cn";

export function PageTitle({ title, desc }: { title: string; desc?: string }) {
  return (
    <div className="mb-5">
      <h1 className="text-xl font-semibold text-text-5">{title}</h1>
      {desc && <p className="mt-1 text-sm text-text-2">{desc}</p>}
    </div>
  );
}

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("mb-4 rounded-lg border border-border bg-bg-1 p-4", className)}>
      {children}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const color =
    status === "success"
      ? "text-success"
      : status === "failed"
      ? "text-danger"
      : "text-warning";
  return <span className={cn("text-xs font-medium", color)}>{status}</span>;
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        "w-full rounded-md border border-border bg-bg-0 px-3 py-2 text-sm text-text-5 outline-none focus:border-accent",
        props.className
      )}
    />
  );
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "w-full rounded-md border border-border bg-bg-0 px-3 py-2 text-sm text-text-5 outline-none focus:border-accent",
        props.className
      )}
    />
  );
}
