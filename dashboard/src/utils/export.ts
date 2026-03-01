/**
 * Export utilities for event log data (JSON and CSV).
 */

import type { EventLogEntry } from "../types/mediwatch";

/**
 * Export event log as a JSON file download.
 */
export function exportAsJSON(
  entries: EventLogEntry[],
  filename = "mediwatch-event-log.json"
): void {
  const json = JSON.stringify(entries, null, 2);
  downloadFile(json, filename, "application/json");
}

/**
 * Export event log as a CSV file download.
 */
export function exportAsCSV(
  entries: EventLogEntry[],
  filename = "mediwatch-event-log.csv"
): void {
  const headers = [
    "ID",
    "Timestamp",
    "Event Type",
    "Severity",
    "Confidence",
    "Description",
    "Detection Model",
    "Acknowledged",
    "Acknowledged At",
    "Acknowledged By",
    "Staff Note",
    "Ack Time (s)",
  ];

  const rows = entries.map((e) =>
    [
      e.id,
      e.timestamp,
      e.eventType,
      e.severity,
      e.confidence.toFixed(2),
      `"${e.description.replace(/"/g, '""')}"`,
      e.detectionModel,
      e.acknowledged ? "Yes" : "No",
      e.acknowledgedAt ?? "",
      e.acknowledgedBy ?? "",
      e.staffNote ? `"${e.staffNote.replace(/"/g, '""')}"` : "",
      e.ackTimeSeconds?.toFixed(1) ?? "",
    ].join(",")
  );

  const csv = [headers.join(","), ...rows].join("\n");
  downloadFile(csv, filename, "text/csv");
}

function downloadFile(
  content: string,
  filename: string,
  mimeType: string
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
