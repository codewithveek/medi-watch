/**
 * useAlerts — Active alerts list, acknowledgment, and escalation timers.
 *
 * Manages the alert state: active alerts sorted by severity,
 * acknowledgment tracking, and escalation countdown.
 */

import { useCallback, useState } from "react";
import type { AlertPayload, EventLogEntry } from "../types/mediwatch";
import { SEVERITY_ORDER } from "../types/mediwatch";

interface UseAlertsReturn {
  activeAlerts: AlertPayload[];
  eventLog: EventLogEntry[];
  addAlert: (alert: AlertPayload) => void;
  acknowledgeAlert: (
    alertId: string,
    staffNote?: string,
    acknowledgedBy?: string
  ) => void;
  markAcknowledged: (alertId: string) => void;
}

export function useAlerts(): UseAlertsReturn {
  const [activeAlerts, setActiveAlerts] = useState<AlertPayload[]>([]);
  const [eventLog, setEventLog] = useState<EventLogEntry[]>([]);

  const addAlert = useCallback((alert: AlertPayload) => {
    setActiveAlerts((prev) => {
      // Deduplicate by ID
      const existing = prev.find((a) => a.id === alert.id);
      if (existing) return prev;

      const updated = [...prev, alert];
      // Sort by severity (highest first), then by timestamp (newest first)
      updated.sort((a, b) => {
        const severityDiff =
          SEVERITY_ORDER[b.severity] - SEVERITY_ORDER[a.severity];
        if (severityDiff !== 0) return severityDiff;
        return (
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
      });
      return updated;
    });

    // Append to event log (append-only, but deduplicate by ID)
    setEventLog((prev) => {
      if (prev.some((e) => e.id === alert.id)) return prev;
      return [...prev, { ...alert, eventType: alert.event_type }];
    });
  }, []);

  const acknowledgeAlert = useCallback(
    (alertId: string, staffNote?: string, acknowledgedBy?: string) => {
      const now = new Date().toISOString();
      const by = acknowledgedBy ?? "staff";

      setActiveAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? { ...a, acknowledged: true, acknowledgedAt: now, staffNote }
            : a
        )
      );

      setEventLog((prev) =>
        prev.map((e) => {
          if (e.id === alertId) {
            const alertTime = new Date(e.timestamp).getTime();
            const ackTime = new Date(now).getTime();
            return {
              ...e,
              acknowledged: true,
              acknowledgedAt: now,
              acknowledgedBy: by,
              staffNote,
              ackTimeSeconds: (ackTime - alertTime) / 1000,
            };
          }
          return e;
        })
      );
    },
    []
  );

  const markAcknowledged = useCallback(
    (alertId: string) => {
      acknowledgeAlert(alertId);
    },
    [acknowledgeAlert]
  );

  return {
    activeAlerts,
    eventLog,
    addAlert,
    acknowledgeAlert,
    markAcknowledged,
  };
}
