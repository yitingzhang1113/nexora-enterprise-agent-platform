"use client";

import useSWR from "swr";
import { LANGFUSE_URL, listTraces } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

export default function TracesPage() {
  const { data: traces } = useSWR<any[]>("traces", listTraces, { refreshInterval: 5000 });

  return (
    <div>
      <PageTitle
        title="Trace"
        desc="每次请求的 LangGraph 节点级链路 (本地兜底)。完整 trace 见 Langfuse。"
      />
      <Card>
        <a href={LANGFUSE_URL} target="_blank" rel="noreferrer" className="text-sm">
          ↗ 打开 Langfuse ({LANGFUSE_URL})
        </a>
      </Card>

      {!traces?.length && <Card>暂无 trace</Card>}
      {traces?.map((t) => (
        <Card key={t.trace_id}>
          <div className="mb-1 flex items-center justify-between">
            <span className="text-sm font-medium text-text-5">{t.question}</span>
            <span className="text-xs text-text-2">
              {t.intent || "-"} · {t.latency_ms}ms
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(t.steps || []).map((s: any, i: number) => (
              <span
                key={i}
                className="rounded-full border border-border bg-bg-0 px-2 py-0.5 text-[11px] text-text-3"
              >
                {s.node} · {s.ms}ms
              </span>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
