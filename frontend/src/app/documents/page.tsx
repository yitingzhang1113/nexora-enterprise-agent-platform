"use client";

import { useEffect, useRef, useState } from "react";
import {
  DocumentItem,
  IndexAttempt,
  indexWeb,
  listAttempts,
  listDocuments,
  uploadFiles,
} from "@/lib/api";

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [attempts, setAttempts] = useState<IndexAttempt[]>([]);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    const [d, a] = await Promise.all([listDocuments(), listAttempts()]);
    setDocs(d);
    setAttempts(a);
  }

  useEffect(() => {
    refresh().catch(() => {});
    const t = setInterval(() => refresh().catch(() => {}), 4000); // 轮询索引状态
    return () => clearInterval(t);
  }, []);

  async function onUpload() {
    const files = fileRef.current?.files;
    if (!files || files.length === 0) return;
    setBusy(true);
    try {
      await uploadFiles(files);
      if (fileRef.current) fileRef.current.value = "";
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function onIndexWeb() {
    if (!url.trim()) return;
    setBusy(true);
    try {
      await indexWeb(url.trim());
      setUrl("");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h3>上传文档 (pdf / txt / md)</h3>
        <div className="row">
          <input ref={fileRef} type="file" multiple />
          <button onClick={onUpload} disabled={busy}>
            上传并索引
          </button>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          上传后会异步切块、嵌入并写入向量库，状态见下方「索引任务」。
        </p>
      </div>

      <div className="card">
        <h3>抓取网页</h3>
        <div className="row">
          <input
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button onClick={onIndexWeb} disabled={busy}>
            抓取并索引
          </button>
        </div>
      </div>

      <div className="card">
        <h3>索引任务</h3>
        {attempts.length === 0 && <p className="muted">暂无</p>}
        {attempts.map((a) => (
          <div key={a.id} className="row" style={{ justifyContent: "space-between" }}>
            <span>#{a.id} (connector {a.connector_id})</span>
            <span className={`status-${a.status}`}>{a.status}</span>
            <span className="muted">
              docs {a.num_docs} / chunks {a.num_chunks}
            </span>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>已索引文档</h3>
        {docs.length === 0 && <p className="muted">暂无</p>}
        {docs.map((d) => (
          <div key={d.id} className="row" style={{ justifyContent: "space-between" }}>
            <span>
              <span className="tag">{d.source}</span>
              {d.title}
            </span>
            <span className="muted">{d.num_chunks} chunks</span>
          </div>
        ))}
      </div>
    </div>
  );
}
