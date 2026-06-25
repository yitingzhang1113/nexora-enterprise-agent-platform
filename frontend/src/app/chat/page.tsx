"use client";

import { useEffect, useRef, useState } from "react";
import {
  Citation,
  Persona,
  chatAgent,
  chatStream,
  listPersonas,
} from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  steps?: string[];
}

export default function ChatPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaId, setPersonaId] = useState<number | undefined>(undefined);
  const [useAgent, setUseAgent] = useState(false);
  const [sessionId, setSessionId] = useState<number | undefined>(undefined);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listPersonas().then(setPersonas).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }]);

    try {
      if (useAgent) {
        const res = await chatAgent({
          message: text,
          session_id: sessionId,
          persona_id: personaId,
        });
        setSessionId(res.session_id);
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            content: res.content,
            citations: res.citations,
            steps: res.steps,
          },
        ]);
      } else {
        // 先放一个空 assistant 气泡，流式填充
        let idx = -1;
        setMessages((m) => {
          idx = m.length;
          return [...m, { role: "assistant", content: "", citations: [] }];
        });
        await chatStream(
          { message: text, session_id: sessionId, persona_id: personaId },
          {
            onMeta: (sid, citations) => {
              setSessionId(sid);
              setMessages((m) => {
                const copy = [...m];
                const last = copy[copy.length - 1];
                if (last && last.role === "assistant") last.citations = citations;
                return copy;
              });
            },
            onToken: (t) => {
              setMessages((m) => {
                const copy = [...m];
                const last = copy[copy.length - 1];
                if (last && last.role === "assistant") last.content += t;
                return copy;
              });
            },
            onDone: () => {},
          }
        );
      }
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `出错了: ${String(e)}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <div className="row" style={{ flexWrap: "wrap", gap: 16 }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <label className="muted">助手 (Persona)</label>
            <select
              value={personaId ?? ""}
              onChange={(e) =>
                setPersonaId(e.target.value ? Number(e.target.value) : undefined)
              }
            >
              <option value="">默认助手</option>
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <label className="row" style={{ gap: 6, marginTop: 18 }}>
            <input
              type="checkbox"
              style={{ width: "auto" }}
              checked={useAgent}
              onChange={(e) => setUseAgent(e.target.checked)}
            />
            <span className="muted">Agent 模式 (工具调用)</span>
          </label>
        </div>
      </div>

      <div className="card" style={{ minHeight: 360 }}>
        {messages.length === 0 && (
          <p className="muted">
            试着问：「二甲双胍的常用起始剂量是多少？」或「布洛芬和华法林能一起用吗？」
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 4 }}>
              {m.role === "user" ? "我" : "助手"}
            </div>
            {m.content || (busy && m.role === "assistant" ? "▍" : "")}
            {m.steps && m.steps.length > 0 && (
              <div className="muted" style={{ marginTop: 8 }}>
                {m.steps.map((s, j) => (
                  <div key={j}>· {s}</div>
                ))}
              </div>
            )}
            {m.citations && m.citations.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div className="muted">引用：</div>
                {m.citations.map((c) => (
                  <div key={c.chunk_id} className="citation">
                    <span className="badge">[{c.n}]</span>
                    <b>{c.document_title}</b>
                    <div style={{ marginTop: 4 }}>
                      {c.content.slice(0, 200)}
                      {c.content.length > 200 ? "…" : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="card">
        <div className="row">
          <textarea
            rows={2}
            placeholder="输入问题，Enter 发送 (Shift+Enter 换行)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button onClick={send} disabled={busy}>
            {busy ? "…" : "发送"}
          </button>
        </div>
      </div>
    </div>
  );
}
