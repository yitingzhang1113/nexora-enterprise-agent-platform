"use client";

import { useRef, useState } from "react";
import useSWR from "swr";
import { DocumentItem, listDocuments, uploadFiles } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, PageTitle } from "@/components/admin/ui";

export default function DocumentsPage() {
  const { data: docs, mutate } = useSWR<DocumentItem[]>("documents", listDocuments, {
    refreshInterval: 4000,
  });
  const fileRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  async function upload() {
    const files = fileRef.current?.files;
    if (!files?.length) return;
    setBusy(true);
    try {
      await uploadFiles(files);
      if (fileRef.current) fileRef.current.value = "";
      mutate();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageTitle title="文档" desc="上传 PDF / TXT / MD，自动切块、嵌入并写入向量库。" />

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">上传文档</div>
        <div className="flex items-center gap-2">
          <input ref={fileRef} type="file" multiple className="text-sm text-text-3" />
          <Button onClick={upload} disabled={busy}>
            上传并索引
          </Button>
        </div>
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">已索引文档</div>
        {!docs?.length && <div className="py-3 text-sm text-text-2">暂无</div>}
        {docs?.map((d) => (
          <div
            key={d.id}
            className="flex items-center justify-between border-b border-border py-2 last:border-0"
          >
            <span className="flex items-center gap-2 text-sm text-text-4">
              <span className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2">
                {d.source}
              </span>
              {d.title}
            </span>
            <span className="text-xs text-text-2">{d.num_chunks} chunks</span>
          </div>
        ))}
      </Card>
    </div>
  );
}
