/**
 * Notification helpers for MediWatch.
 */

import type { AlertPayload } from "../types/mediwatch";

/**
 * Play a browser audio notification for alerts.
 * Uses the Web Audio API for a simple alert tone.
 */
export function playAlertSound(severity: AlertPayload["severity"]): void {
  try {
    const ctx = new AudioContext();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    // Frequency based on severity
    const freqMap: Record<string, number> = {
      CRITICAL: 880,
      HIGH: 660,
      MEDIUM: 440,
      LOW: 330,
    };

    oscillator.frequency.value = freqMap[severity] ?? 440;
    oscillator.type = "sine";
    gain.gain.value = 0.3;

    oscillator.start();

    // Duration based on severity
    const duration = severity === "CRITICAL" ? 1.0 : 0.5;
    oscillator.stop(ctx.currentTime + duration);

    // Cleanup
    setTimeout(() => ctx.close(), (duration + 0.5) * 1000);
  } catch {
    // Audio may not be available — fail silently
  }
}

/**
 * Format a timestamp for display.
 */
export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

/**
 * Format seconds to human-readable duration.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600)
    return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}
