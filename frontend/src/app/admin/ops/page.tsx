"use client";

import useSWR from "swr";
import { listOpsTickets } from "@/lib/api";
import { Card, PageTitle, StatusBadge } from "@/components/admin/ui";

export default function OpsPage() {
  const { data } = useSWR<any[]>("ops-tickets", listOpsTickets, { refreshInterval: 4000 });
  return (
    <div>
      <PageTitle title="运营工单" desc="Agent 自动创建或人工创建的运营工单。" />
      {!data?.length && <Card>暂无工单</Card>}
      {data?.map((t) => (
        <Card key={t.id}>
          <div className="flex items-center justify-between">
            <span className="font-medium text-text-5">#{t.id} {t.title}</span>
            <span className="flex items-center gap-2 text-xs text-text-2">
              {t.sku && <span className="rounded-full border border-border px-2 py-0.5">{t.sku}</span>}
              <span className="rounded-full border border-border px-2 py-0.5">{t.severity}</span>
              <StatusBadge status={t.status === "open" ? "running" : "success"} />
            </span>
          </div>
          {t.body && <p className="mt-1 text-sm text-text-3">{t.body}</p>}
        </Card>
      ))}
    </div>
  );
}
