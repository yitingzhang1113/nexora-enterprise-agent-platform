"use client";

import {
  ChartBar,
  ChartLine,
  ChatCircleDots,
  Database,
  FileText,
  Pulse,
  Robot,
  ShieldCheck,
  Ticket,
  Wrench,
} from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const items = [
  { href: "/admin/dashboard", label: "运营看板", icon: ChartBar },
  { href: "/admin/documents", label: "知识库", icon: FileText },
  { href: "/admin/data", label: "业务数据", icon: Database },
  { href: "/admin/tools", label: "工具注册表", icon: Wrench },
  { href: "/admin/ops", label: "运营工单", icon: Ticket },
  { href: "/admin/approvals", label: "审批队列", icon: ShieldCheck },
  { href: "/admin/slack", label: "Slack 通知", icon: ChatCircleDots },
  { href: "/admin/agents", label: "助手", icon: Robot },
  { href: "/admin/traces", label: "Trace", icon: Pulse },
  { href: "/admin/status", label: "系统状态", icon: ChartLine },
];

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav className="w-52 shrink-0 border-r border-border bg-bg-1 p-3">
      <div className="px-2 pb-3 pt-1 text-xs font-semibold uppercase tracking-wide text-text-2">
        Ops 管理后台
      </div>
      {items.map((it) => {
        const Icon = it.icon;
        const active = pathname === it.href;
        return (
          <Link
            key={it.href}
            href={it.href}
            className={cn(
              "mb-1 flex items-center gap-2 rounded-md px-2.5 py-2 text-sm",
              active ? "bg-accent-soft text-text-5" : "text-text-3 hover:bg-bg-2"
            )}
          >
            <Icon size={16} /> {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
