"use client";

import { CheckCircle, Cube, User, Wrench } from "@phosphor-icons/react";
import ReactMarkdown from "react-markdown";
import type { Citation, NodeStep, ToolStep } from "@/lib/api";
import { useUI } from "@/lib/store";

export interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  nodes?: NodeStep[];
  tools?: ToolStep[];
  streaming?: boolean;
}

export function Message({ msg }: { msg: ChatMsg }) {
  const { setSources, openSources } = useUI();
  const isUser = msg.role === "user";

  return (
    <div className="animate-in py-5">
      <div className="mx-auto flex max-w-chat gap-3 px-4">
        <div
          className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${
            isUser ? "bg-bg-3 text-text-4" : "bg-accent text-white"
          }`}
        >
          {isUser ? <User size={16} /> : <Cube size={16} weight="fill" />}
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1 text-xs font-medium text-text-2">
            {isUser ? "我" : "Nexora 助手"}
          </div>

          {/* LangGraph 流程时间线 */}
          {!isUser && msg.nodes && msg.nodes.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1.5">
              {msg.nodes.map((n, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-full border border-border bg-bg-1 px-2 py-0.5 text-[11px] text-text-3"
                >
                  <CheckCircle size={11} className="text-success" /> {n.label}
                </span>
              ))}
            </div>
          )}

          {/* 工具调用结果 */}
          {msg.tools && msg.tools.length > 0 && (
            <div className="mb-2 space-y-1">
              {msg.tools.map((t, i) => (
                <div
                  key={i}
                  className="rounded-md border border-border bg-bg-1 px-2.5 py-1.5 text-xs text-text-3"
                >
                  <div className="flex items-center gap-1.5">
                    <Wrench size={13} className="text-accent" />
                    <code className="text-text-5">{t.name}</code>
                    <span className="text-text-2">{JSON.stringify(t.args)}</span>
                  </div>
                  <div className="mt-1 text-text-4">{t.output}</div>
                </div>
              ))}
            </div>
          )}

          {isUser ? (
            <div className="whitespace-pre-wrap text-text-5">{msg.content}</div>
          ) : (
            <div className="prose-chat text-text-5">
              <ReactMarkdown>{msg.content || (msg.streaming ? "▍" : "")}</ReactMarkdown>
            </div>
          )}

          {msg.citations && msg.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              <span className="text-xs text-text-2">来源:</span>
              {msg.citations.map((c) => (
                <button
                  key={c.chunk_id}
                  onClick={() => {
                    setSources(msg.citations!);
                    openSources();
                  }}
                  title={c.document_title}
                  className="rounded-full border border-border bg-bg-1 px-2 py-0.5 text-xs text-text-3 hover:bg-bg-2"
                >
                  [{c.n}] {c.document_title.slice(0, 20)}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
