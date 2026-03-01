/**
 * useAuditLog — Append-only event log with export capabilities.
 *
 * The audit log is append-only (no deletion). Supports JSON and CSV export.
 */

import { useCallback, useState } from "react";
import type { AuditEntry } from "../types/mediwatch";

interface UseAuditLogReturn {
  entries: AuditEntry[];
  addEntry: (entry: AuditEntry) => void;
  addEntries: (entries: AuditEntry[]) => void;
  exportJSON: () => string;
  exportCSV: () => string;
}

export function useAuditLog(): UseAuditLogReturn {
  const [entries, setEntries] = useState<AuditEntry[]>([]);

  const addEntry = useCallback((entry: AuditEntry) => {
    setEntries((prev) => [...prev, entry]);
  }, []);

  const addEntries = useCallback((newEntries: AuditEntry[]) => {
    setEntries((prev) => [...prev, ...newEntries]);
  }, []);

  const exportJSON = useCallback(() => {
    return JSON.stringify(entries, null, 2);
  }, [entries]);

  const exportCSV = useCallback(() => {
    const headers = ["alertId", "timestamp", "channel", "status", "error"];
    const rows = entries.map((e) =>
      [e.alertId, e.timestamp, e.channel, e.status, e.error ?? ""].join(",")
    );
    return [headers.join(","), ...rows].join("\n");
  }, [entries]);

  return { entries, addEntry, addEntries, exportJSON, exportCSV };
}
