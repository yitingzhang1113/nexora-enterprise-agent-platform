import { AppShell } from "@/components/AppShell";
import { AdminNav } from "@/components/admin/AdminNav";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <div className="flex h-full min-h-0 flex-1">
        <AdminNav />
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </div>
    </AppShell>
  );
}
