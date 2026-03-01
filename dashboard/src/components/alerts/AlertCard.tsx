import React, { useEffect, useRef, useState } from "react";
import SeverityBadge from "../shared/SeverityBadge";
import ConfidenceMeter from "../shared/ConfidenceMeter";
import { EVENT_TYPE_LABELS } from "../../types/mediwatch";
import type { AlertPayload } from "../../types/mediwatch";
import { formatTimestamp } from "../../utils/notifications";

interface AlertCardProps {
  alert: AlertPayload;
  onAcknowledge: (id: string, staffNote?: string) => void;
}

/**
 * Individual alert card with severity badge, confidence meter,
 * escalation timer, and acknowledge action.
 */
const AlertCard: React.FC<AlertCardProps> = ({ alert, onAcknowledge }) => {
  const [staffNote, setStaffNote] = useState("");
  const [showNote, setShowNote] = useState(false);

  return (
    <div
      className={`card border-l-4 transition-all ${getBorderColor(
        alert.severity
      )}`}
      role="alert"
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={alert.severity} size="sm" />
            <span className="text-xs text-mw-text-secondary">
              {formatTimestamp(alert.timestamp)}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-mw-text-primary">
            {EVENT_TYPE_LABELS[alert.event_type] ?? alert.event_type}
          </h3>
        </div>
        <ConfidenceMeter value={alert.confidence} compact />
      </div>

      {/* Description */}
      <p className="mt-2 text-xs leading-relaxed text-mw-text-secondary">
        {alert.description}
      </p>

      {/* Escalation timer for unacknowledged HIGH/CRITICAL */}
      {(alert.severity === "HIGH" || alert.severity === "CRITICAL") && (
        <EscalationTimer alertTimestamp={alert.timestamp} />
      )}

      {/* Staff note + acknowledge */}
      <div className="mt-3 flex items-center gap-2">
        {showNote ? (
          <input
            type="text"
            value={staffNote}
            onChange={(e) => setStaffNote(e.target.value)}
            placeholder="Optional staff note…"
            className="flex-1 rounded border border-mw-surface-2 bg-mw-surface-2 px-2 py-1 text-xs text-mw-text-primary placeholder:text-mw-text-secondary/50 focus:border-mw-accent focus:outline-none"
            onKeyDown={(e) => {
              if (e.key === "Enter")
                onAcknowledge(alert.id, staffNote || undefined);
            }}
          />
        ) : (
          <button
            onClick={() => setShowNote(true)}
            className="text-[10px] text-mw-text-secondary hover:text-mw-text-primary transition-colors"
          >
            + Add note
          </button>
        )}
        <button
          onClick={() => onAcknowledge(alert.id, staffNote || undefined)}
          className="btn-primary ml-auto whitespace-nowrap text-xs"
        >
          Acknowledge
        </button>
      </div>
    </div>
  );
};

/**
 * Shows a countdown to voice escalation (90 seconds from alert time).
 */
const EscalationTimer: React.FC<{ alertTimestamp: string }> = ({
  alertTimestamp,
}) => {
  const escalationSeconds = 90;
  const alertTime = useRef(new Date(alertTimestamp).getTime());
  const [remaining, setRemaining] = useState(() => {
    const elapsed = (Date.now() - alertTime.current) / 1000;
    return Math.max(0, escalationSeconds - elapsed);
  });

  useEffect(() => {
    if (remaining <= 0) return;
    const interval = setInterval(() => {
      const elapsed = (Date.now() - alertTime.current) / 1000;
      const left = Math.max(0, escalationSeconds - elapsed);
      setRemaining(left);
      if (left <= 0) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }, [remaining]);

  if (remaining <= 0) {
    return (
      <div className="mt-2 flex items-center gap-1.5 text-[10px] font-medium text-red-400">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
        Voice escalation triggered
      </div>
    );
  }

  const pct = ((escalationSeconds - remaining) / escalationSeconds) * 100;

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[10px] text-mw-text-secondary">
        <span>Voice escalation in</span>
        <span className="font-mono font-medium text-orange-400">
          {Math.ceil(remaining)}s
        </span>
      </div>
      <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-mw-surface-2">
        <div
          className="h-full rounded-full bg-orange-500 transition-all duration-1000"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

function getBorderColor(severity: string): string {
  switch (severity) {
    case "CRITICAL":
      return "border-red-500";
    case "HIGH":
      return "border-orange-500";
    case "MEDIUM":
      return "border-yellow-500";
    case "LOW":
      return "border-blue-500";
    default:
      return "border-mw-surface-2";
  }
}

export default AlertCard;
