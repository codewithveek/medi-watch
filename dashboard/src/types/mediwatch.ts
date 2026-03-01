/**
 * MediWatch shared TypeScript types.
 *
 * These types mirror the backend AlertPayload schema.
 * Never use `any` — use these types or `unknown` and narrow.
 */

// --- Enums ---

export type EventType = "FALL" | "IMMOBILITY" | "DISTRESS" | "IV_INTERFERENCE";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AlertChannel =
  | "DASHBOARD"
  | "BROWSER_PUSH"
  | "VOICE"
  | "SMS"
  | "CALL";

export type AgentStatus = "ONLINE" | "OFFLINE" | "DEGRADED";

export type ConnectionStatus =
  | "connected"
  | "connecting"
  | "disconnected"
  | "error";

// --- Payloads ---

export interface FrameMetadata {
  poseKeypoints: number[][];
  boundingBox: number[];
  detectionZone: string;
}

export interface AlertPayload {
  id: string;
  timestamp: string;
  event_type: EventType;
  severity: Severity;
  confidence: number;
  detectionModel: string;
  description: string;
  frameMetadata: FrameMetadata;
  alertChannels: AlertChannel[];
  acknowledged: boolean;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  staffNote?: string;
  disclaimer: string;
}

export interface MetricsPayload {
  events_total: number;
  alerts_sent: number;
  alerts_acknowledged: number;
  fps: number | null;
  latency_ms: number | null;
  uptime_seconds: number | null;
  events_detected: number;
  active_alerts: number;
  agent_status: AgentStatus | string | null;
  active_model: string | null;
}

export interface AgentStatusPayload {
  status: AgentStatus;
  activeModel: string;
  uptime: number;
}

// --- WebSocket messages ---

export type AgentMessage =
  | { type: "alert"; payload: AlertPayload }
  | { type: "metrics"; payload: MetricsPayload }
  | { type: "agent_status"; payload: AgentStatusPayload }
  | {
      type: "ack_confirmed";
      payload: {
        alert_id: string;
        acknowledged_at: string;
        acknowledged_by: string;
      };
    };

export type DashboardMessage =
  | {
      type: "acknowledge";
      alert_id: string;
      staff_note?: string;
      acknowledged_by?: string;
    }
  | { type: "settings_update"; settings: Partial<AgentSettings> };

// --- Settings ---

export interface AgentSettings {
  fallConfidenceThreshold: number;
  immobilityTimeoutSeconds: number;
  distressConfidenceThreshold: number;
  cooldownSeconds: number;
  dashboardEnabled: boolean;
  smsEnabled: boolean;
  voiceEnabled: boolean;
  ttsEnabled: boolean;
  nursePhone: string;
  doctorPhone: string;
  llmProvider: "openai" | "gemini";
  poseModel: string;
}

// --- Audit ---

export interface AuditEntry {
  alertId: string;
  timestamp: string;
  channel: string;
  status: "sent" | "failed";
  error?: string;
}

// --- UI State ---

export interface EventLogEntry extends AlertPayload {
  eventType: EventType;
  ackTimeSeconds?: number;
}

// --- Severity helpers ---

export const SEVERITY_ORDER: Record<Severity, number> = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

export const SEVERITY_COLORS: Record<Severity, string> = {
  CRITICAL: "#ff4d4d",
  HIGH: "#ff8c42",
  MEDIUM: "#ffd166",
  LOW: "#06d6a0",
};

export const SEVERITY_BG_COLORS: Record<Severity, string> = {
  CRITICAL: "rgba(255, 77, 77, 0.15)",
  HIGH: "rgba(255, 140, 66, 0.15)",
  MEDIUM: "rgba(255, 209, 102, 0.15)",
  LOW: "rgba(6, 214, 160, 0.15)",
};

export const SEVERITY_ICONS: Record<Severity, string> = {
  CRITICAL: "🔴",
  HIGH: "🟠",
  MEDIUM: "🟡",
  LOW: "🟢",
};

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  FALL: "Fall Detected",
  IMMOBILITY: "Prolonged Immobility",
  DISTRESS: "Distress Signal",
  IV_INTERFERENCE: "IV/Tube Interference",
};
