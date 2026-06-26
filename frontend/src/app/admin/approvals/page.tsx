"use client";

import { useState } from "react";
import useSWR from "swr";
import { ApprovalItem, approveApproval, listApprovals, rejectApproval } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, PageTitle, StatusBadge } from "@/components/admin/ui";

export default function ApprovalsPage() {
  const { data, mutate } = useSWR<ApprovalItem[]>("approvals", listApprovals, {
    refreshInterval: 4000,
  });
  const [busy, setBusy] = useState<number | null>(null);

  async function act(id: number, fn: (id: number) => Promise<any>) {
    setBusy(id);
    try {
      await fn(id);
      mutate();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageTitle title="审批队列" desc="高风险动作(退款>$200、暂停广告)需人工审批。通过即执行并通知 Slack。" />
      {!data?.length && <Card>暂无审批</Card>}
      {data?.map((a) => (
        <Card key={a.id}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-text-5">{a.title}</span>
                <span className="rounded-full border border-border px-2 py-0.5 text-xs text-text-2">
                  {a.action_type}
                </span>
                <StatusBadge status={a.status === "executed" ? "success" : a.status === "rejected" ? "failed" : "pending"} />
              </div>
              <div className="mt-1 text-xs text-text-2">{JSON.stringify(a.payload)}</div>
              {a.result ? (
                <div className="mt-1 text-xs text-text-3">结果: {JSON.stringify(a.result)}</div>
              ) : null}
            </div>
            {a.status === "pending" && (
              <div className="flex gap-2">
                <Button onClick={() => act(a.id, approveApproval)} disabled={busy === a.id}>
                  通过
                </Button>
                <Button variant="secondary" onClick={() => act(a.id, rejectApproval)} disabled={busy === a.id}>
                  拒绝
                </Button>
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
