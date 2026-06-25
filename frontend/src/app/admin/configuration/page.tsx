"use client";

import useSWR from "swr";
import { getCurrentLlm, getSearchSettings } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

export default function ConfigurationPage() {
  const { data: llm } = useSWR("llm", getCurrentLlm);
  const { data: search } = useSWR("search-settings", getSearchSettings);

  return (
    <div>
      <PageTitle title="配置" desc="当前模型与向量库设置 (学习版只读)。" />

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">语言模型 (LiteLLM)</div>
        <KV k="模型" v={llm?.model} />
        <KV k="Provider" v={llm?.provider} />
        <KV k="嵌入模型" v={llm?.embed_model} />
        <KV k="嵌入维度" v={llm?.embed_dim} />
      </Card>

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">向量库 (OpenSearch)</div>
        <KV k="后端" v={search?.backend} />
        <KV k="索引名" v={search?.index_name} />
        <KV k="chunk 总数" v={search?.chunk_count} />
        <KV k="Top-K" v={search?.top_k} />
      </Card>
    </div>
  );
}

function KV({ k, v }: { k: string; v: any }) {
  return (
    <div className="flex justify-between border-b border-border py-2 text-sm last:border-0">
      <span className="text-text-2">{k}</span>
      <span className="font-mono text-text-5">{v ?? "—"}</span>
    </div>
  );
}
