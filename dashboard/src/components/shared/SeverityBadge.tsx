import React from "react";
import {
  SEVERITY_COLORS,
  SEVERITY_BG_COLORS,
  SEVERITY_ICONS,
} from "../../types/mediwatch";
import type { Severity } from "../../types/mediwatch";

interface SeverityBadgeProps {
  severity: Severity;
  /** Show the icon alongside the label */
  showIcon?: boolean;
  /** Size variant */
  size?: "sm" | "md";
}

/**
 * Color-coded severity badge with icon and label.
 */
const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  showIcon = true,
  size = "md",
}) => {
  const textColor = SEVERITY_COLORS[severity];
  const bgColor = SEVERITY_BG_COLORS[severity];
  const icon = SEVERITY_ICONS[severity];

  const sizeClasses =
    size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${sizeClasses}`}
      style={{ color: textColor, backgroundColor: bgColor }}
    >
      {showIcon && <span className="text-xs">{icon}</span>}
      {severity}
    </span>
  );
};

export default SeverityBadge;
