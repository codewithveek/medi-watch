import React from "react";
import AlertCard from "./AlertCard";
import type { AlertPayload } from "../../types/mediwatch";

interface AlertPanelProps {
  alerts: AlertPayload[];
  onAcknowledge: (id: string, staffNote?: string) => void;
}

/**
 * Panel displaying all active (unacknowledged) alerts, sorted by severity.
 */
const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onAcknowledge }) => {
  return (
    <div className="card flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-mw-text-primary">
          Active Alerts
        </h2>
        {alerts.length > 0 && (
          <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400">
            {alerts.length}
          </span>
        )}
      </div>

      {alerts.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-mw-text-secondary">
          <svg
            className="h-10 w-10 opacity-30"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-xs">No active alerts</p>
        </div>
      ) : (
        <div className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto pr-1">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={onAcknowledge}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
