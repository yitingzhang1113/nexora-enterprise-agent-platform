"use client";

import useSWR from "swr";
import { listToolsRegistry } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

export default function ToolsPage() {
  const { data } = useSWR<any[]>("tools", listToolsRegistry, { refreshInterval: 5000 });
  return (
    <div>
      <PageTitle title="工具注册表" desc="MCP 工具的 schema 与调用计数。带「动作」标记的为有副作用工具。" />
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {data?.map((t) => (
          <Card key={t.name} className="mb-0">
            <div className="flex items-center gap-2">
              <code className="font-medium text-text-5">{t.name}</code>
              {t.is_action && (
                <span className="rounded-full bg-warning/20 px-2 py-0.5 text-[11px] text-warning">动作</span>
              )}
              <span className="ml-auto text-xs text-text-2">调用 {t.call_count}</span>
            </div>
            <p className="mt-1 text-sm text-text-3">{t.description}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
