"use client";

import { useRef, useState } from "react";
import useSWR from "swr";
import {
  DocumentItem,
  IndexAttempt,
  indexWeb,
  listAttempts,
  listDocuments,
  uploadFiles,
} from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, Input, PageTitle, StatusBadge } from "@/components/admin/ui";

export default function KnowledgePage() {
  const { data: docs, mutate: md } = useSWR<DocumentItem[]>("documents", listDocuments, {
    refreshInterval: 4000,
  });
  const { data: attempts, mutate: ma } = useSWR<IndexAttempt[]>("attempts", listAttempts, {
    refreshInterval: 4000,
  });
  const fileRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);

  async function upload() {
    const files = fileRef.current?.files;
    if (!files?.length) return;
    setBusy(true);
    try {
      await uploadFiles(files);
      if (fileRef.current) fileRef.current.value = "";
      md();
      ma();
    } finally {
      setBusy(false);
    }
  }

  async function addWeb() {
    if (!url.trim()) return;
    setBusy(true);
    try {
      await indexWeb(url.trim());
      setUrl("");
      md();
      ma();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageTitle title="知识库" desc="上传文档或抓取网页 → 切块/嵌入 → 写入 Milvus + Postgres。" />

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">上传文档 (pdf/txt/md)</div>
        <div className="flex items-center gap-2">
          <input ref={fileRef} type="file" multiple className="text-sm text-text-3" />
          <Button onClick={upload} disabled={busy}>上传并索引</Button>
        </div>
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">抓取网页</div>
        <div className="flex gap-2">
          <Input placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} />
          <Button onClick={addWeb} disabled={busy}>抓取并索引</Button>
        </div>
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">索引任务</div>
        {!attempts?.length && <Empty />}
        {attempts?.map((a) => (
          <div key={a.id} className="flex items-center justify-between border-b border-border py-2 last:border-0">
            <span className="text-sm text-text-4">#{a.id} · connector {a.connector_id}</span>
            <span className="flex items-center gap-3 text-xs text-text-2">
              docs {a.num_docs} / chunks {a.num_chunks}
              <StatusBadge status={a.status} />
            </span>
          </div>
        ))}
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">已索引文档</div>
        {!docs?.length && <Empty />}
        {docs?.map((d) => (
          <div key={d.id} className="flex items-center justify-between border-b border-border py-2 last:border-0">
            <span className="flex items-center gap-2 text-sm text-text-4">
              <span className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2">{d.source}</span>
              {d.title}
            </span>
            <span className="text-xs text-text-2">{d.num_chunks} chunks</span>
          </div>
        ))}
      </Card>
    </div>
  );
}

function Empty() {
  return <div className="py-3 text-sm text-text-2">暂无</div>;
}
