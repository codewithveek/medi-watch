import React, { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { EVENT_TYPE_LABELS } from "../types/mediwatch";
import type { EventLogEntry, MetricsPayload } from "../types/mediwatch";

interface AnalyticsProps {
  entries: EventLogEntry[];
  metrics: MetricsPayload | null;
}

const EVENT_COLORS: Record<string, string> = {
  FALL: "#ef4444",
  IMMOBILITY: "#f97316",
  DISTRESS: "#eab308",
  IV_INTERFERENCE: "#3b82f6",
};

/**
 * Analytics dashboard with hourly chart, event type distribution,
 * and KPI metric cards.
 */
const Analytics: React.FC<AnalyticsProps> = ({ entries, metrics }) => {
  // Events per hour (last 24 hours)
  const hourlyData = useMemo(() => {
    const now = Date.now();
    const buckets: Record<string, number> = {};

    // Create 24 hour buckets
    for (let i = 23; i >= 0; i--) {
      const d = new Date(now - i * 3600_000);
      const key = `${d.getHours().toString().padStart(2, "0")}:00`;
      buckets[key] = 0;
    }

    entries.forEach((e) => {
      const d = new Date(e.timestamp);
      if (now - d.getTime() <= 24 * 3600_000) {
        const key = `${d.getHours().toString().padStart(2, "0")}:00`;
        if (key in buckets) buckets[key]++;
      }
    });

    return Object.entries(buckets).map(([hour, count]) => ({ hour, count }));
  }, [entries]);

  // Event type distribution
  const typeDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    entries.forEach((e) => {
      counts[e.eventType] = (counts[e.eventType] ?? 0) + 1;
    });
    return Object.entries(counts).map(([type, count]) => ({
      name: EVENT_TYPE_LABELS[type as keyof typeof EVENT_TYPE_LABELS] ?? type,
      value: count,
      color: EVENT_COLORS[type] ?? "#6b7280",
    }));
  }, [entries]);

  // KPI calculations
  const totalEvents = entries.length;
  const acknowledgedCount = entries.filter((e) => e.acknowledged).length;
  const ackRate =
    totalEvents > 0
      ? ((acknowledgedCount / totalEvents) * 100).toFixed(1)
      : "—";
  const avgConfidence =
    totalEvents > 0
      ? (
          (entries.reduce((sum, e) => sum + e.confidence, 0) / totalEvents) *
          100
        ).toFixed(1)
      : "—";
  const avgAckTime = (() => {
    const acked = entries.filter((e) => e.ackTimeSeconds != null);
    if (acked.length === 0) return "—";
    const avg =
      acked.reduce((sum, e) => sum + (e.ackTimeSeconds ?? 0), 0) / acked.length;
    return `${avg.toFixed(1)}s`;
  })();

  return (
    <div className="flex flex-col gap-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KPICard label="Total Events" value={String(totalEvents)} />
        <KPICard label="Ack Rate" value={`${ackRate}%`} />
        <KPICard label="Avg Confidence" value={`${avgConfidence}%`} />
        <KPICard label="Avg Ack Time" value={avgAckTime} />
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Events per Hour */}
        <div className="card">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
            Events Per Hour (24h)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: "#9ca3af" }}
                interval={2}
              />
              <YAxis
                tick={{ fontSize: 10, fill: "#9ca3af" }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Event Type Distribution */}
        <div className="card">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
            Event Type Distribution
          </h3>
          {typeDistribution.length === 0 ? (
            <div className="flex h-[200px] items-center justify-center text-xs text-mw-text-secondary">
              No data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={typeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {typeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    fontSize: 12,
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11 }}
                  formatter={(value) => (
                    <span style={{ color: "#d1d5db" }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Agent Metrics */}
      {metrics && (
        <div className="card">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
            Agent Performance
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KPICard label="FPS" value={metrics.fps?.toFixed(1) ?? "—"} small />
            <KPICard
              label="Latency"
              value={
                metrics.latency_ms ? `${Math.round(metrics.latency_ms)}ms` : "—"
              }
              small
            />
            <KPICard
              label="Agent Status"
              value={metrics.agent_status ?? "—"}
              small
            />
            <KPICard
              label="Active Alerts"
              value={String(metrics.active_alerts ?? 0)}
              small
            />
          </div>
        </div>
      )}
    </div>
  );
};

const KPICard: React.FC<{ label: string; value: string; small?: boolean }> = ({
  label,
  value,
  small = false,
}) => (
  <div className="rounded-lg bg-mw-surface-2 px-3 py-2">
    <p className="text-[10px] uppercase tracking-wider text-mw-text-secondary">
      {label}
    </p>
    <p
      className={`mt-1 font-mono font-bold text-mw-text-primary ${
        small ? "text-sm" : "text-lg"
      }`}
    >
      {value}
    </p>
  </div>
);

export default Analytics;
