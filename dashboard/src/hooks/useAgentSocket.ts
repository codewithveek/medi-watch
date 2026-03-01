/**
 * useAgentSocket — WebSocket connection lifecycle and message routing.
 *
 * Manages the real-time connection between the dashboard and the agent backend.
 * Routes inbound messages to appropriate handlers.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentMessage,
  AgentStatusPayload,
  AlertPayload,
  ConnectionStatus,
  MetricsPayload,
} from "../types/mediwatch";

const DEFAULT_WS_URL =
  import.meta.env.VITE_AGENT_WS_URL ?? "ws://localhost:8080/ws";
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

interface UseAgentSocketOptions {
  url?: string;
  onAlert?: (alert: AlertPayload) => void;
  onMetrics?: (metrics: MetricsPayload) => void;
  onAgentStatus?: (status: AgentStatusPayload) => void;
  onAckConfirmed?: (alertId: string) => void;
  onFrame?: (frameData: string) => void;
}

interface UseAgentSocketReturn {
  status: ConnectionStatus;
  sendMessage: (msg: Record<string, unknown>) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useAgentSocket(
  options: UseAgentSocketOptions
): UseAgentSocketReturn {
  const wsUrl = options.url ?? DEFAULT_WS_URL;

  const [status, setStatus] = useState<ConnectionStatus>("disconnected");

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Stable references for callbacks
  const callbackRefs = useRef(options);
  callbackRefs.current = options;

  const sendMessage = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const manualDisconnect = useRef(false);

  const disconnect = useCallback(() => {
    manualDisconnect.current = true;
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("disconnected");
    console.log("[MediWatch] WebSocket manually disconnected");
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    manualDisconnect.current = false;
    setStatus("connecting");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      reconnectAttempts.current = 0;
      console.log("[MediWatch] WebSocket connected");
      // Resume camera stream on (re)connect
      ws.send(JSON.stringify({ type: "STREAM_RESUME" }));
    };

    ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        // Normalize type to lowercase — backend sends UPPERCASE, frontend uses lowercase
        const msg = { ...raw, type: raw.type?.toLowerCase() } as AgentMessage;

        switch (msg.type) {
          case "alert":
            callbackRefs.current.onAlert?.(msg.payload);
            break;
          case "metrics":
            callbackRefs.current.onMetrics?.(msg.payload);
            break;
          case "agent_status":
            callbackRefs.current.onAgentStatus?.(msg.payload);
            break;
          case "ack_confirmed":
            callbackRefs.current.onAckConfirmed?.(msg.payload.alert_id);
            break;
          case "frame":
            callbackRefs.current.onFrame?.(msg.payload.data);
            break;
        }
      } catch (err) {
        console.error("[MediWatch] Failed to parse WebSocket message:", err);
      }
    };

    ws.onclose = () => {
      console.log("[MediWatch] WebSocket disconnected");

      // Only auto-reconnect if not manually disconnected
      if (
        !manualDisconnect.current &&
        reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS
      ) {
        setStatus("connecting");
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      } else {
        setStatus("disconnected");
      }
    };

    ws.onerror = () => {
      setStatus("error");
    };
  }, [wsUrl]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    status,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}
