"use client";

import { PaperPlaneRight } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { chatStream, listPersonas, Persona } from "@/lib/api";
import { useUI } from "@/lib/store";
import { ChatMsg, Message } from "./Message";
import { SourcesPanel } from "./SourcesPanel";

export function ChatMain() {
  const { personaId, sessionId, setSession, newChatNonce, setSources } = useUI();
  const { data: personas } = useSWR<Persona[]>("personas", listPersonas);
  const persona = personas?.find((p) => p.id === personaId);

  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMessages([]), [newChatNonce]);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setMessages((m) => [
      ...m,
      { role: "assistant", content: "", streaming: true, nodes: [], tools: [] },
    ]);

    const patch = (fn: (m: ChatMsg) => void) =>
      setMessages((cur) => {
        const copy = [...cur];
        const last = copy[copy.length - 1];
        if (last && last.role === "assistant") fn(last);
        return copy;
      });

    try {
      await chatStream(
        { message: text, session_id: sessionId, persona_id: personaId },
        {
          onMeta: (sid) => setSession(sid),
          onNode: (n) => patch((m) => (m.nodes = [...(m.nodes || []), n])),
          onTool: (t) => patch((m) => (m.tools = [...(m.tools || []), t])),
          onCitations: (c) => {
            patch((m) => (m.citations = c));
            setSources(c);
          },
          onApproval: (a) => patch((m) => (m.approvals = [...(m.approvals || []), a])),
          onToken: (t) => patch((m) => (m.content += t)),
          onClarification: (text) => patch((m) => (m.content = text)),
          onDone: () => patch((m) => (m.streaming = false)),
        }
      );
    } catch (e) {
      patch((m) => {
        m.content = `出错了: ${String(e)}`;
        m.streaming = false;
      });
    } finally {
      setBusy(false);
      patch((m) => (m.streaming = false));
    }
  }

  return (
    <div className="flex h-full min-w-0 flex-1">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="text-sm font-medium text-text-5">{persona?.name || "运营助手"}</div>
          <div className="text-xs text-text-2">Ops Agent · 规划/并行工具/审批</div>
        </header>

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <Welcome personaName={persona?.name} />
          ) : (
            messages.map((m, i) => <Message key={i} msg={m} />)
          )}
          <div ref={endRef} />
        </div>

        <div className="px-4 pb-5 pt-2">
          <div className="mx-auto flex max-w-chat items-end gap-2 rounded-lg border border-border bg-bg-1 p-2">
            <textarea
              rows={1}
              placeholder="给助手发消息… (Enter 发送, Shift+Enter 换行)"
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
            助手会自动判断意图: 知识问答 / 工具调用 / 闲聊 / 请求澄清。
          </p>
        </div>
      </div>

      <SourcesPanel />
    </div>
  );
}

function Welcome({ personaName }: { personaName?: string }) {
  const samples = [
    "分析最近 7 天异常商品, 风险高就建工单并通知 Slack",
    "NX-AIR-FRYER-001 的退货率是多少？原因是什么？",
    "订单 10086 退款 $300 能退吗？需要审批吗？",
    "退款超过多少需要经理审批？",
  ];
  return (
    <div className="mx-auto flex h-full max-w-chat flex-col items-center justify-center px-4 text-center">
      <h1 className="mb-2 text-2xl font-semibold text-text-5">{personaName || "运营助手"}</h1>
      <p className="mb-6 text-sm text-text-2">
        电商运营多工具 Agent: 规划 → 并行工具 → 校验 → 审批 → 执行, 由 LangGraph 编排。
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
