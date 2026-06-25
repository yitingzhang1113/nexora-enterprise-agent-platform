"use client";

import { Database, FileText, Gear, Robot } from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const items = [
  { href: "/admin/connectors", label: "连接器", icon: Database },
  { href: "/admin/documents", label: "文档", icon: FileText },
  { href: "/admin/agents", label: "助手", icon: Robot },
  { href: "/admin/configuration", label: "配置", icon: Gear },
];

export function AdminNav() {
  const pathname = usePathname();
  return (
    <nav className="w-52 shrink-0 border-r border-border bg-bg-1 p-3">
      <div className="px-2 pb-3 pt-1 text-xs font-semibold uppercase tracking-wide text-text-2">
        管理后台
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
