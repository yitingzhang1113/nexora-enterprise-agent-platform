"use client";

import { useState } from "react";
import useSWR from "swr";
import { IndexAttempt, indexWeb, listAttempts, listConnectors } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, Input, PageTitle, StatusBadge } from "@/components/admin/ui";

export default function ConnectorsPage() {
  const { data: connectors, mutate: mc } = useSWR("connectors", listConnectors);
  const { data: attempts, mutate: ma } = useSWR<IndexAttempt[]>("attempts", listAttempts, {
    refreshInterval: 4000,
  });
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);

  async function addWeb() {
    if (!url.trim()) return;
    setBusy(true);
    try {
      await indexWeb(url.trim());
      setUrl("");
      mc();
      ma();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageTitle title="连接器" desc="管理数据源。新增网页连接器会异步抓取并索引到 OpenSearch。" />

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">新增网页连接器</div>
        <div className="flex gap-2">
          <Input
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <Button onClick={addWeb} disabled={busy}>
            抓取并索引
          </Button>
        </div>
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">已配置连接器</div>
        {!connectors?.length && <Empty />}
        {connectors?.map((c) => (
          <Row key={c.id} left={`${c.name}`} mid={c.source} right={`#${c.id}`} />
        ))}
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">索引任务</div>
        {!attempts?.length && <Empty />}
        {attempts?.map((a) => (
          <div
            key={a.id}
            className="flex items-center justify-between border-b border-border py-2 last:border-0"
          >
            <span className="text-sm text-text-4">
              #{a.id} · connector {a.connector_id}
            </span>
            <span className="flex items-center gap-3 text-xs text-text-2">
              docs {a.num_docs} / chunks {a.num_chunks}
              <StatusBadge status={a.status} />
            </span>
          </div>
        ))}
      </Card>
    </div>
  );
}

function Row({ left, mid, right }: { left: string; mid: string; right: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2 last:border-0">
      <span className="text-sm text-text-4">{left}</span>
      <span className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2">
        {mid}
      </span>
      <span className="text-xs text-text-2">{right}</span>
    </div>
  );
}

function Empty() {
  return <div className="py-3 text-sm text-text-2">暂无</div>;
}
