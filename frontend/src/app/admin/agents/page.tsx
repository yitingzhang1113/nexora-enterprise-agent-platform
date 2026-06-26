"use client";

import { useState } from "react";
import useSWR from "swr";
import { createPersona, listPersonas, Persona } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, Input, PageTitle, Textarea } from "@/components/admin/ui";

const ALL_TOOLS = ["get_weather", "query_ticket", "query_sales"];

export default function AgentsPage() {
  const { data: personas, mutate } = useSWR<Persona[]>("personas", listPersonas);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [prompt, setPrompt] = useState(
    "你是一个严谨的企业知识助手，依据参考资料作答并标注引用 [n]。"
  );
  const [tools, setTools] = useState<string[]>(["get_weather"]);
  const [busy, setBusy] = useState(false);

  async function create() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await createPersona({ name: name.trim(), description: desc, system_prompt: prompt, tools });
      setName("");
      setDesc("");
      mutate();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageTitle title="助手 (Persona)" desc="每个助手有自己的 system prompt 与可用工具。" />

      <Card>
        <div className="mb-3 text-sm font-medium text-text-5">新建助手</div>
        <label className="mb-1 block text-xs text-text-2">名称</label>
        <Input value={name} onChange={(e) => setName(e.target.value)} className="mb-3" />
        <label className="mb-1 block text-xs text-text-2">描述</label>
        <Input value={desc} onChange={(e) => setDesc(e.target.value)} className="mb-3" />
        <label className="mb-1 block text-xs text-text-2">System Prompt</label>
        <Textarea rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} className="mb-3" />
        <div className="mb-3 flex items-center gap-4">
          <span className="text-xs text-text-2">工具:</span>
          {ALL_TOOLS.map((t) => (
            <label key={t} className="flex items-center gap-1.5 text-sm text-text-3">
              <input
                type="checkbox"
                checked={tools.includes(t)}
                onChange={() =>
                  setTools((cur) =>
                    cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]
                  )
                }
              />
              {t}
            </label>
          ))}
        </div>
        <Button onClick={create} disabled={busy}>
          创建
        </Button>
      </Card>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">已有助手</div>
        {!personas?.length && <div className="py-3 text-sm text-text-2">暂无</div>}
        {personas?.map((p) => (
          <div key={p.id} className="border-b border-border py-3 last:border-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-text-5">{p.name}</span>
              {p.tools.map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2"
                >
                  {t}
                </span>
              ))}
            </div>
            <p className="mt-1 text-sm text-text-3">{p.description}</p>
            <p className="mt-1 text-xs text-text-2">{p.system_prompt}</p>
          </div>
        ))}
      </Card>
    </div>
  );
}
