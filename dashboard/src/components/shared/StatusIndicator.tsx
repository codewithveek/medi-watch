import React from "react";
import type { ConnectionStatus } from "../../types/mediwatch";

interface StatusIndicatorProps {
  status: ConnectionStatus;
  /** Optional label override */
  label?: string;
}

const STATUS_CONFIG: Record<
  ConnectionStatus,
  { color: string; pulse: boolean; label: string }
> = {
  connected: { color: "bg-green-500", pulse: true, label: "Connected" },
  connecting: { color: "bg-yellow-500", pulse: true, label: "Connecting…" },
  disconnected: { color: "bg-red-500", pulse: false, label: "Disconnected" },
  error: { color: "bg-red-600", pulse: false, label: "Error" },
};

/**
 * Connection status indicator with a pulsing dot.
 */
const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, label }) => {
  const config = STATUS_CONFIG[status];

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {config.pulse && (
          <span
            className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${config.color}`}
          />
        )}
        <span
          className={`relative inline-flex h-2.5 w-2.5 rounded-full ${config.color}`}
        />
      </span>
      <span className="text-xs font-medium text-mw-text-secondary">
        {label ?? config.label}
      </span>
    </div>
  );
};

export default StatusIndicator;
