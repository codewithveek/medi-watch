import React, { useState, useMemo } from "react";
import SeverityBadge from "./shared/SeverityBadge";
import ConfidenceMeter from "./shared/ConfidenceMeter";
import { EVENT_TYPE_LABELS } from "../types/mediwatch";
import type { EventLogEntry, Severity, EventType } from "../types/mediwatch";
import { formatTimestamp } from "../utils/notifications";
import { exportAsJSON, exportAsCSV } from "../utils/export";

interface EventLogProps {
  entries: EventLogEntry[];
}

type SortField = "timestamp" | "severity" | "confidence";
type SortDir = "asc" | "desc";

const SEVERITY_RANK: Record<string, number> = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

/**
 * Sortable + filterable event log table with export functionality.
 */
const EventLog: React.FC<EventLogProps> = ({ entries }) => {
  const [sortField, setSortField] = useState<SortField>("timestamp");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [filterSeverity, setFilterSeverity] = useState<Severity | "ALL">("ALL");
  const [filterType, setFilterType] = useState<EventType | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredAndSorted = useMemo(() => {
    let result = [...entries];

    // Filter by severity
    if (filterSeverity !== "ALL") {
      result = result.filter((e) => e.severity === filterSeverity);
    }

    // Filter by event type
    if (filterType !== "ALL") {
      result = result.filter((e) => e.eventType === filterType);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (e) =>
          e.description.toLowerCase().includes(q) ||
          e.eventType.toLowerCase().includes(q) ||
          (e.staffNote?.toLowerCase().includes(q) ?? false)
      );
    }

    // Sort
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "timestamp":
          cmp =
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case "severity":
          cmp =
            (SEVERITY_RANK[a.severity] ?? 0) - (SEVERITY_RANK[b.severity] ?? 0);
          break;
        case "confidence":
          cmp = a.confidence - b.confidence;
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

    return result;
  }, [entries, sortField, sortDir, filterSeverity, filterType, searchQuery]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <div className="card flex flex-col gap-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-mw-text-primary">
          Event Log
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => exportAsJSON(entries)}
            className="rounded-md bg-mw-surface-2 px-2.5 py-1 text-xs font-medium text-mw-text-secondary hover:text-mw-text-primary transition-colors"
          >
            Export JSON
          </button>
          <button
            onClick={() => exportAsCSV(entries)}
            className="rounded-md bg-mw-surface-2 px-2.5 py-1 text-xs font-medium text-mw-text-secondary hover:text-mw-text-primary transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          placeholder="Search events…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2.5 py-1 text-xs text-mw-text-primary placeholder:text-mw-text-secondary/50 focus:border-mw-accent focus:outline-none"
        />
        <select
          value={filterSeverity}
          onChange={(e) =>
            setFilterSeverity(e.target.value as Severity | "ALL")
          }
          className="rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2 py-1 text-xs text-mw-text-primary focus:border-mw-accent focus:outline-none"
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as EventType | "ALL")}
          className="rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2 py-1 text-xs text-mw-text-primary focus:border-mw-accent focus:outline-none"
        >
          <option value="ALL">All Types</option>
          <option value="FALL">Fall</option>
          <option value="IMMOBILITY">Immobility</option>
          <option value="DISTRESS">Distress</option>
          <option value="IV_INTERFERENCE">IV Interference</option>
        </select>
        <span className="ml-auto text-[10px] text-mw-text-secondary">
          {filteredAndSorted.length} of {entries.length} events
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-mw-surface-2 text-[10px] uppercase tracking-wider text-mw-text-secondary">
              <th
                className="cursor-pointer px-2 py-2 hover:text-mw-text-primary"
                onClick={() => toggleSort("timestamp")}
              >
                Time{sortIndicator("timestamp")}
              </th>
              <th className="px-2 py-2">Type</th>
              <th
                className="cursor-pointer px-2 py-2 hover:text-mw-text-primary"
                onClick={() => toggleSort("severity")}
              >
                Severity{sortIndicator("severity")}
              </th>
              <th
                className="cursor-pointer px-2 py-2 hover:text-mw-text-primary"
                onClick={() => toggleSort("confidence")}
              >
                Confidence{sortIndicator("confidence")}
              </th>
              <th className="px-2 py-2">Description</th>
              <th className="px-2 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-2 py-8 text-center text-mw-text-secondary"
                >
                  No events found
                </td>
              </tr>
            )}
            {filteredAndSorted.map((entry) => (
              <tr
                key={entry.id}
                className="border-b border-mw-surface-2/50 hover:bg-mw-surface-2/30 transition-colors"
              >
                <td className="whitespace-nowrap px-2 py-2 font-mono text-mw-text-secondary">
                  {formatTimestamp(entry.timestamp)}
                </td>
                <td className="px-2 py-2 text-mw-text-primary">
                  {EVENT_TYPE_LABELS[entry.eventType] ?? entry.eventType}
                </td>
                <td className="px-2 py-2">
                  <SeverityBadge severity={entry.severity} size="sm" />
                </td>
                <td className="px-2 py-2">
                  <ConfidenceMeter value={entry.confidence} compact />
                </td>
                <td className="max-w-[200px] truncate px-2 py-2 text-mw-text-secondary">
                  {entry.description}
                </td>
                <td className="px-2 py-2">
                  {entry.acknowledged ? (
                    <span className="text-green-400">✓ Ack</span>
                  ) : (
                    <span className="text-orange-400">Pending</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EventLog;
