import React, { useState } from "react";
import StatusIndicator from "./shared/StatusIndicator";
import type { ConnectionStatus, MetricsPayload } from "../types/mediwatch";
import { formatDuration } from "../utils/notifications";

interface LiveFeedProps {
  status: ConnectionStatus;
  metrics: MetricsPayload | null;
  /** Base64 frame data from agent (optional — placeholder if none) */
  frameData?: string;
}

/**
 * Live video feed panel with connection status and optional YOLO overlay toggle.
 */
const LiveFeed: React.FC<LiveFeedProps> = ({ status, metrics, frameData }) => {
  const [showOverlay, setShowOverlay] = useState(true);

  return (
    <div className="card flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-mw-text-primary">
            Live Feed
          </h2>
          <StatusIndicator status={status} />
        </div>
        <button
          onClick={() => setShowOverlay((v) => !v)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
            showOverlay
              ? "bg-mw-accent/20 text-mw-accent"
              : "bg-mw-surface-2 text-mw-text-secondary"
          }`}
        >
          {showOverlay ? "Overlay ON" : "Overlay OFF"}
        </button>
      </div>

      {/* Video Area */}
      <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
        {frameData ? (
          <img
            src={`data:image/jpeg;base64,${frameData}`}
            alt="Live patient monitoring feed"
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            {status === "connected" ? (
              <div className="text-center text-mw-text-secondary">
                <svg
                  className="mx-auto h-12 w-12 opacity-40"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"
                  />
                </svg>
                <p className="mt-2 text-xs">Waiting for video frames…</p>
              </div>
            ) : (
              <div className="text-center text-mw-text-secondary">
                <div className="mx-auto h-12 w-12 rounded-full border-2 border-red-500/30 flex items-center justify-center">
                  <svg
                    className="h-6 w-6 text-red-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636"
                    />
                  </svg>
                </div>
                <p className="mt-2 text-xs">Not connected</p>
              </div>
            )}
          </div>
        )}

        {/* Overlay indicator */}
        {showOverlay && frameData && (
          <div className="absolute bottom-2 left-2 rounded bg-black/60 px-2 py-0.5 text-[10px] text-green-400 backdrop-blur">
            YOLO Overlay Active
          </div>
        )}
      </div>

      {/* Metrics Bar */}
      {metrics && (
        <div className="grid grid-cols-4 gap-2 text-center">
          <MetricItem label="FPS" value={metrics.fps?.toFixed(1) ?? "—"} />
          <MetricItem
            label="Latency"
            value={
              metrics.latency_ms ? `${Math.round(metrics.latency_ms)}ms` : "—"
            }
          />
          <MetricItem
            label="Uptime"
            value={
              metrics.uptime_seconds
                ? formatDuration(metrics.uptime_seconds)
                : "—"
            }
          />
          <MetricItem
            label="Events"
            value={String(metrics.events_detected ?? 0)}
          />
        </div>
      )}
    </div>
  );
};

const MetricItem: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <div className="rounded-md bg-mw-surface-2 px-2 py-1.5">
    <p className="text-[10px] uppercase tracking-wider text-mw-text-secondary">
      {label}
    </p>
    <p className="mt-0.5 font-mono text-sm font-semibold text-mw-text-primary">
      {value}
    </p>
  </div>
);

export default LiveFeed;
