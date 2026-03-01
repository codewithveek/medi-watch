/**
 * usePushNotifications — Web Notifications API + Vibration API for haptic alerts.
 *
 * Rules:
 * - Permission requested on first load
 * - If denied, falls back gracefully to in-page alerts only
 * - Never repeatedly prompts after denial
 * - Haptic pattern: [200, 100, 200] for HIGH/CRITICAL, [100] for LOW/MEDIUM
 * - Always guard navigator.vibrate calls
 */

import { useCallback, useEffect, useState } from "react";
import type { AlertPayload, Severity } from "../types/mediwatch";

interface UsePushNotificationsReturn {
  permission: NotificationPermission | "unsupported";
  requestPermission: () => Promise<void>;
  notify: (alert: AlertPayload) => void;
}

const HAPTIC_HIGH: number[] = [200, 100, 200];
const HAPTIC_LOW: number[] = [100];

function getHapticPattern(severity: Severity): number[] {
  return severity === "CRITICAL" || severity === "HIGH"
    ? HAPTIC_HIGH
    : HAPTIC_LOW;
}

export function usePushNotifications(): UsePushNotificationsReturn {
  const [permission, setPermission] = useState<
    NotificationPermission | "unsupported"
  >(() => {
    if (typeof window === "undefined" || !("Notification" in window)) {
      return "unsupported";
    }
    return Notification.permission;
  });

  const requestPermission = useCallback(async () => {
    if (
      permission === "unsupported" ||
      permission === "granted" ||
      permission === "denied"
    ) {
      return;
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
    } catch {
      console.warn("[MediWatch] Notification permission request failed");
    }
  }, [permission]);

  // Request permission on mount (once)
  useEffect(() => {
    if (permission === "default") {
      requestPermission();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const notify = useCallback(
    (alert: AlertPayload) => {
      // Browser push notification
      if (permission === "granted") {
        try {
          const _notification = new Notification(
            `⚠️ MediWatch: ${alert.event_type}`,
            {
              body: `${
                alert.description
              } — AI-Assisted, verify immediately. Confidence: ${(
                alert.confidence * 100
              ).toFixed(0)}%`,
              icon: `/icons/severity-${alert.severity.toLowerCase()}.png`,
              tag: alert.id,
              requireInteraction: alert.severity === "CRITICAL",
            }
          );
          // Keep reference to prevent GC
          void _notification;
        } catch {
          console.warn("[MediWatch] Failed to show notification");
        }
      }

      // Haptic feedback (always guard)
      navigator.vibrate?.(getHapticPattern(alert.severity));
    },
    [permission]
  );

  return { permission, requestPermission, notify };
}
