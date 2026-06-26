"use client";

import useSWR from "swr";
import { listSlack } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

export default function SlackPage() {
  const { data } = useSWR<any[]>("slack", listSlack, { refreshInterval: 4000 });
  return (
    <div>
      <PageTitle title="Slack 通知" desc="Agent 发往运营频道的通知 (mock; 配 SLACK_WEBHOOK_URL 则真发)。" />
      {!data?.length && <Card>暂无通知</Card>}
      {data?.map((m) => (
        <Card key={m.id} className="mb-2">
          <div className="flex items-center gap-2 text-xs text-text-2">
            <span className="rounded-full bg-accent-soft px-2 py-0.5 text-text-5">{m.channel}</span>
            {m.sent_real ? "已真发" : "mock"}
            <span className="ml-auto">{m.created_at?.slice(0, 19).replace("T", " ")}</span>
          </div>
          <p className="mt-1 text-sm text-text-4">{m.text}</p>
        </Card>
      ))}
    </div>
  );
}
