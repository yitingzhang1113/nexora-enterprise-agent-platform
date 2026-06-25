"use client";

import { FileText, X } from "@phosphor-icons/react";
import { useUI } from "@/lib/store";
import { IconButton } from "@/components/ui/IconButton";

export function SourcesPanel() {
  const { sources, sourcesOpen, closeSources } = useUI();
  if (!sourcesOpen) return null;

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-l border-border bg-bg-1">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <span className="flex items-center gap-2 text-sm font-medium text-text-5">
          <FileText size={16} /> 引用来源 ({sources.length})
        </span>
        <IconButton onClick={closeSources} aria-label="关闭">
          <X size={16} />
        </IconButton>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {sources.map((c) => (
          <div
            key={c.chunk_id}
            id={`cite-${c.n}`}
            className="mb-3 rounded-md border border-border bg-bg-0 p-3"
          >
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded-full bg-accent-soft px-2 py-0.5 text-xs text-text-5">
                [{c.n}]
              </span>
              <span className="truncate text-sm font-medium text-text-5">
                {c.document_title}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-text-3">
              {c.content.slice(0, 260)}
              {c.content.length > 260 ? "…" : ""}
            </p>
          </div>
        ))}
      </div>
    </aside>
  );
}
