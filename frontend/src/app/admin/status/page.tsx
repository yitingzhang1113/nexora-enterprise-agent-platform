"use client";

import useSWR from "swr";
import { getStatus } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

export default function StatusPage() {
  const { data } = useSWR<any>("status", getStatus, { refreshInterval: 5000 });

  return (
    <div>
      <PageTitle title="系统状态" desc="模型路由 / 熔断 / 向量库 / 服务健康。" />

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">模型路由 (LLM Router)</div>
        <KV k="Provider" v={data?.llm_router?.provider} />
        <KV k="主力模型" v={data?.llm_router?.main_model} />
        <KV k="轻任务模型" v={data?.llm_router?.fast_model} />
        <KV k="熔断状态" v={data?.llm_router?.breaker} />
      </Card>

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">向量库 (Milvus)</div>
        <KV k="后端" v={data?.vector_db?.backend} />
        <KV k="集合" v={data?.vector_db?.collection} />
        <KV k="向量数" v={data?.vector_db?.count} />
      </Card>

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">服务健康</div>
        <KV k="Ollama" v={data?.ollama?.ok ? `ok (${(data.ollama.models || []).join(", ")})` : "down"} />
        <KV k="Model Server" v={data?.model_server?.ok ? "ok" : "down"} />
        <KV k="Langfuse" v={data?.langfuse_enabled ? "enabled" : "disabled"} />
      </Card>

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">节点调用计数</div>
        {data?.metrics &&
          Object.entries(data.metrics).map(([k, v]) => <KV key={k} k={k} v={v as any} />)}
      </Card>
    </div>
  );
}

function KV({ k, v }: { k: string; v: any }) {
  return (
    <div className="flex justify-between border-b border-border py-2 text-sm last:border-0">
      <span className="text-text-2">{k}</span>
      <span className="font-mono text-text-5">{String(v ?? "—")}</span>
    </div>
  );
}
