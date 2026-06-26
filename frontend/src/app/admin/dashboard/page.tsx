"use client";

import useSWR from "swr";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDashboard } from "@/lib/api";
import { Card, PageTitle } from "@/components/admin/ui";

const AXIS = "#8a93a6";
const GRID = "#262b36";

export default function DashboardPage() {
  const { data } = useSWR<any>("dashboard", getDashboard, { refreshInterval: 8000 });
  const kpis = data?.kpis || {};

  return (
    <div>
      <PageTitle title="运营看板" desc="销量趋势 / 退货率 / 库存水位 / 关键指标 (实时来自 Postgres)。" />

      {/* KPI 卡片 */}
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Kpi label="订单总数" value={kpis.total_orders} />
        <Kpi label="退货总数" value={kpis.total_returns} />
        <Kpi label="整体退货率" value={kpis.overall_return_rate != null ? `${kpis.overall_return_rate}%` : "—"} />
        <Kpi label="低库存 SKU" value={kpis.low_stock_skus} warn />
      </div>

      <Card>
        <div className="mb-2 text-sm font-medium text-text-5">近 14 天销量趋势 (整体 vs 异常 SKU)</div>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data?.sales_trend || []}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="date" stroke={AXIS} fontSize={12} />
            <YAxis stroke={AXIS} fontSize={12} />
            <Tooltip contentStyle={{ background: "#171a21", border: "1px solid #262b36" }} />
            <Legend />
            <Line type="monotone" dataKey="units" name="整体销量" stroke="#4f8cff" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="anomaly" name="NX-AIR-FRYER-001" stroke="#ff6b6b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-2 text-sm font-medium text-text-5">退货率 Top SKU (%)</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data?.return_rate || []}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
              <XAxis dataKey="sku" stroke={AXIS} fontSize={10} angle={-15} textAnchor="end" height={50} />
              <YAxis stroke={AXIS} fontSize={12} />
              <Tooltip contentStyle={{ background: "#171a21", border: "1px solid #262b36" }} />
              <ReferenceLine y={10} stroke="#ffcc66" strokeDasharray="4 4" label={{ value: "10% 阈值", fill: "#ffcc66", fontSize: 11 }} />
              <Bar dataKey="rate" name="退货率%">
                {(data?.return_rate || []).map((d: any, i: number) => (
                  <Cell key={i} fill={d.rate >= 10 ? "#ff6b6b" : "#4f8cff"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <div className="mb-2 text-sm font-medium text-text-5">库存水位 (最低 8 个 SKU)</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data?.inventory || []}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
              <XAxis dataKey="sku" stroke={AXIS} fontSize={10} angle={-15} textAnchor="end" height={50} />
              <YAxis stroke={AXIS} fontSize={12} />
              <Tooltip contentStyle={{ background: "#171a21", border: "1px solid #262b36" }} />
              <Legend />
              <Bar dataKey="stock" name="库存">
                {(data?.inventory || []).map((d: any, i: number) => (
                  <Cell key={i} fill={d.below ? "#ff6b6b" : "#57d68a"} />
                ))}
              </Bar>
              <Bar dataKey="safety" name="安全线" fill="#3d4456" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

function Kpi({ label, value, warn }: { label: string; value: any; warn?: boolean }) {
  return (
    <Card className="mb-0 text-center">
      <div className={`text-2xl font-semibold ${warn && value ? "text-danger" : "text-text-5"}`}>
        {value ?? "—"}
      </div>
      <div className="mt-1 text-xs text-text-2">{label}</div>
    </Card>
  );
}
