"use client";

import { useEffect, useState } from "react";
import { Persona, createPersona, listPersonas } from "@/lib/api";

const ALL_TOOLS = ["search_docs", "calculator"];

export default function AssistantsPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [prompt, setPrompt] = useState(
    "你是一个严谨的医药知识助手，依据参考资料作答并标注引用 [n]。"
  );
  const [tools, setTools] = useState<string[]>(["search_docs"]);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setPersonas(await listPersonas());
  }
  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  async function onCreate() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await createPersona({
        name: name.trim(),
        description: desc,
        system_prompt: prompt,
        tools,
      });
      setName("");
      setDesc("");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  function toggleTool(t: string) {
    setTools((cur) =>
      cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]
    );
  }

  return (
    <div className="container">
      <div className="card">
        <h3>新建助手 (Persona)</h3>
        <label className="muted">名称</label>
        <input value={name} onChange={(e) => setName(e.target.value)} />
        <label className="muted" style={{ marginTop: 10, display: "block" }}>
          描述
        </label>
        <input value={desc} onChange={(e) => setDesc(e.target.value)} />
        <label className="muted" style={{ marginTop: 10, display: "block" }}>
          System Prompt
        </label>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <div style={{ marginTop: 10 }}>
          <span className="muted">工具：</span>
          {ALL_TOOLS.map((t) => (
            <label key={t} className="row" style={{ display: "inline-flex", gap: 4, marginRight: 14 }}>
              <input
                type="checkbox"
                style={{ width: "auto" }}
                checked={tools.includes(t)}
                onChange={() => toggleTool(t)}
              />
              {t}
            </label>
          ))}
        </div>
        <div style={{ marginTop: 12 }}>
          <button onClick={onCreate} disabled={busy}>
            创建
          </button>
        </div>
      </div>

      <div className="card">
        <h3>已有助手</h3>
        {personas.length === 0 && <p className="muted">暂无</p>}
        {personas.map((p) => (
          <div key={p.id} className="citation">
            <b>{p.name}</b>{" "}
            {p.tools.map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
            <div className="muted">{p.description}</div>
            <div style={{ marginTop: 4, fontSize: 13 }}>{p.system_prompt}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
