"use client";

import { PaperPlaneRight, Sparkle } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { chatStream, listPersonas, Persona } from "@/lib/api";
import { useUI } from "@/lib/store";
import { ChatMsg, Message } from "./Message";
import { SourcesPanel } from "./SourcesPanel";

export function ChatMain() {
  const { personaId, sessionId, setSession, useAgent, setUseAgent, newChatNonce, setSources } =
    useUI();
  const { data: personas } = useSWR<Persona[]>("personas", listPersonas);
  const persona = personas?.find((p) => p.id === personaId);

  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  // 新建对话: 清空
  useEffect(() => {
    setMessages([]);
  }, [newChatNonce]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setMessages((m) => [...m, { role: "assistant", content: "", streaming: true, tools: [] }]);

    const patchLast = (fn: (m: ChatMsg) => void) =>
      setMessages((cur) => {
        const copy = [...cur];
        const last = copy[copy.length - 1];
        if (last && last.role === "assistant") fn(last);
        return copy;
      });

    try {
      await chatStream(
        { message: text, session_id: sessionId, persona_id: personaId, use_agent: useAgent },
        {
          onMeta: (sid) => setSession(sid),
          onTool: (step) => patchLast((m) => (m.tools = [...(m.tools || []), step])),
          onCitations: (cites) => {
            patchLast((m) => (m.citations = cites));
            setSources(cites);
          },
          onToken: (t) => patchLast((m) => (m.content += t)),
          onDone: () => patchLast((m) => (m.streaming = false)),
        }
      );
    } catch (e) {
      patchLast((m) => {
        m.content = `出错了: ${String(e)}`;
        m.streaming = false;
      });
    } finally {
      setBusy(false);
      patchLast((m) => (m.streaming = false));
    }
  }

  return (
    <div className="flex h-full min-w-0 flex-1">
      <div className="flex min-w-0 flex-1 flex-col">
        {/* 顶栏 */}
        <header className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="text-sm font-medium text-text-5">
            {persona?.name || "默认助手"}
          </div>
          <button
            onClick={() => setUseAgent(!useAgent)}
            className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs transition-colors ${
              useAgent
                ? "border-accent bg-accent-soft text-text-5"
                : "border-border text-text-3 hover:bg-bg-2"
            }`}
          >
            <Sparkle size={14} weight={useAgent ? "fill" : "regular"} /> Agent 模式
          </button>
        </header>

        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <Welcome personaName={persona?.name} />
          ) : (
            messages.map((m, i) => <Message key={i} msg={m} />)
          )}
          <div ref={endRef} />
        </div>

        {/* 输入条 */}
        <div className="px-4 pb-5 pt-2">
          <div className="mx-auto flex max-w-chat items-end gap-2 rounded-lg border border-border bg-bg-1 p-2">
            <textarea
              rows={1}
              placeholder="给医药助手发消息… (Enter 发送, Shift+Enter 换行)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-text-5 outline-none placeholder:text-text-2"
            />
            <button
              onClick={send}
              disabled={busy || !input.trim()}
              className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-white hover:bg-accent-hover disabled:opacity-40"
            >
              <PaperPlaneRight size={16} weight="fill" />
            </button>
          </div>
          <p className="mx-auto mt-2 max-w-chat text-center text-xs text-text-2">
            示例数据为合成资料, 仅供学习, 非医学建议。
          </p>
        </div>
      </div>

      <SourcesPanel />
    </div>
  );
}

function Welcome({ personaName }: { personaName?: string }) {
  const samples = [
    "二甲双胍的常用起始剂量是多少？",
    "布洛芬和华法林一起用有什么风险？",
    "阿莫西林成人怎么服用？",
  ];
  return (
    <div className="mx-auto flex h-full max-w-chat flex-col items-center justify-center px-4 text-center">
      <h1 className="mb-2 text-2xl font-semibold text-text-5">
        {personaName || "医药知识助手"}
      </h1>
      <p className="mb-6 text-sm text-text-2">
        基于内部药品资料的检索增强问答, 回答带可溯源引用。
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {samples.map((s) => (
          <span
            key={s}
            className="rounded-full border border-border bg-bg-1 px-3 py-1.5 text-xs text-text-3"
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}
