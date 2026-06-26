"use client";

import {
  ChatCircleDots,
  Cube,
  Gear,
  NotePencil,
  Robot,
  Sidebar as SidebarIcon,
} from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import useSWR from "swr";
import { cn } from "@/lib/cn";
import { listPersonas, listSessions, Persona, ChatSession } from "@/lib/api";
import { useUI } from "@/lib/store";
import { IconButton } from "@/components/ui/IconButton";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function AppSidebar() {
  const { sidebarOpen, toggleSidebar, personaId, setPersona, setSession, newChat } = useUI();
  const pathname = usePathname();
  const { data: personas } = useSWR<Persona[]>("personas", listPersonas);
  const { data: sessions } = useSWR<ChatSession[]>("sessions", listSessions);

  if (!sidebarOpen) {
    return (
      <div className="flex h-screen w-12 flex-col items-center gap-2 border-r border-border bg-bg-1 py-3">
        <IconButton onClick={toggleSidebar} aria-label="展开侧栏">
          <SidebarIcon size={18} />
        </IconButton>
        <IconButton onClick={newChat} aria-label="新建对话">
          <NotePencil size={18} />
        </IconButton>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-64 flex-col border-r border-border bg-bg-1">
      {/* 头部 */}
      <div className="flex items-center justify-between px-3 py-3">
        <Link href="/" className="flex items-center gap-2 font-semibold text-text-5">
          <Cube size={20} weight="fill" className="text-accent" /> Nexora
        </Link>
        <IconButton onClick={toggleSidebar} aria-label="收起侧栏">
          <SidebarIcon size={18} />
        </IconButton>
      </div>

      {/* 新建对话 */}
      <div className="px-3">
        <Link href="/">
          <button
            onClick={newChat}
            className="flex w-full items-center gap-2 rounded-md border border-border bg-bg-0 px-3 py-2 text-sm text-text-5 hover:bg-bg-2"
          >
            <NotePencil size={16} /> 新建对话
          </button>
        </Link>
      </div>

      {/* 助手 */}
      <SectionLabel icon={<Robot size={14} />} text="助手" />
      <div className="px-2">
        {(personas || []).map((p) => (
          <button
            key={p.id}
            onClick={() => {
              setPersona(p.id);
              setSession(undefined);
            }}
            className={cn(
              "flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm",
              personaId === p.id ? "bg-accent-soft text-text-5" : "text-text-3 hover:bg-bg-2"
            )}
          >
            <Robot size={15} /> <span className="truncate">{p.name}</span>
          </button>
        ))}
        {!personas?.length && <Empty text="暂无助手" />}
      </div>

      {/* 历史 */}
      <SectionLabel icon={<ChatCircleDots size={14} />} text="对话历史" />
      <div className="flex-1 overflow-y-auto px-2">
        {(sessions || []).map((s) => (
          <button
            key={s.id}
            onClick={() => setSession(s.id)}
            className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm text-text-3 hover:bg-bg-2"
          >
            <span className="truncate">{s.title || `会话 #${s.id}`}</span>
          </button>
        ))}
        {!sessions?.length && <Empty text="暂无历史" />}
      </div>

      {/* 底部 */}
      <div className="border-t border-border px-2 py-2">
        <Link
          href="/admin/connectors"
          className={cn(
            "flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm",
            pathname.startsWith("/admin")
              ? "bg-accent-soft text-text-5"
              : "text-text-3 hover:bg-bg-2"
          )}
        >
          <Gear size={16} /> 管理后台
        </Link>
        <div className="mt-1 flex items-center justify-between px-1">
          <span className="text-xs text-text-2">demo@nexora.local</span>
          <ThemeToggle />
        </div>
      </div>
    </div>
  );
}

function SectionLabel({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-1.5 px-4 pb-1 pt-4 text-xs font-medium uppercase tracking-wide text-text-2">
      {icon} {text}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="px-3 py-2 text-xs text-text-2">{text}</div>;
}
