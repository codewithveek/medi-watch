import React from "react";

interface ConfidenceMeterProps {
  /** Confidence value between 0 and 1 */
  value: number;
  /** Compact mode for inline use */
  compact?: boolean;
}

function getConfidenceColor(value: number): string {
  if (value >= 0.8) return "bg-green-500";
  if (value >= 0.6) return "bg-yellow-500";
  if (value >= 0.4) return "bg-orange-500";
  return "bg-red-500";
}

/**
 * Visual confidence meter showing detection confidence as a progress bar.
 */
const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  value,
  compact = false,
}) => {
  const pct = Math.round(value * 100);
  const barColor = getConfidenceColor(value);

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-mw-text-secondary">
        <span className="inline-block h-1.5 w-12 rounded-full bg-mw-surface-2 overflow-hidden">
          <span
            className={`block h-full rounded-full ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </span>
        {pct}%
      </span>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 rounded-full bg-mw-surface-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="min-w-[3ch] text-right text-xs font-mono text-mw-text-secondary">
        {pct}%
      </span>
    </div>
  );
};

export default ConfidenceMeter;
