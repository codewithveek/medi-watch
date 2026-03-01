import React, { useState, useCallback } from "react";
import DisclaimerBanner from "./components/shared/DisclaimerBanner";
import StatusIndicator from "./components/shared/StatusIndicator";
import LiveFeed from "./components/LiveFeed";
import AlertPanel from "./components/alerts/AlertPanel";
import EventLog from "./components/EventLog";
import Analytics from "./components/Analytics";
import Settings from "./components/settings/Settings";
import { useAgentSocket } from "./hooks/useAgentSocket";
import { useAlerts } from "./hooks/useAlerts";
import { usePushNotifications } from "./hooks/usePushNotifications";
import type {
  AgentSettings,
  MetricsPayload,
  AlertPayload,
} from "./types/mediwatch";
import { playAlertSound } from "./utils/notifications";

type Tab = "monitor" | "events" | "analytics" | "settings";

const DEFAULT_SETTINGS: AgentSettings = {
  fallConfidenceThreshold: 0.7,
  immobilityTimeoutSeconds: 120,
  distressConfidenceThreshold: 0.65,
  cooldownSeconds: 30,
  dashboardEnabled: true,
  smsEnabled: false,
  voiceEnabled: false,
  ttsEnabled: false,
  nursePhone: "",
  doctorPhone: "",
  llmProvider: "openai",
  poseModel: "yolo11n-pose",
};

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("monitor");
  const [metrics, setMetrics] = useState<MetricsPayload | null>(null);
  const [agentSettings, setAgentSettings] =
    useState<AgentSettings>(DEFAULT_SETTINGS);

  const { activeAlerts, eventLog, addAlert, acknowledgeAlert } = useAlerts();
  const { notify } = usePushNotifications();

  // Handle incoming alert
  const handleAlert = useCallback(
    (alert: AlertPayload) => {
      addAlert(alert);
      playAlertSound(alert.severity);
      notify(alert);
    },
    [addAlert, notify]
  );

  // Handle incoming metrics
  const handleMetrics = useCallback((m: MetricsPayload) => {
    setMetrics(m);
  }, []);

  // WebSocket connection
  const { status, sendMessage } = useAgentSocket({
    url: `ws://${window.location.hostname}:8080/ws`,
    onAlert: handleAlert,
    onMetrics: handleMetrics,
  });

  // Acknowledge alert handler
  const handleAcknowledge = useCallback(
    (id: string, staffNote?: string) => {
      acknowledgeAlert(id, staffNote, "Dashboard User");
      sendMessage({
        type: "acknowledge",
        alert_id: id,
        staff_note: staffNote,
      });
    },
    [acknowledgeAlert, sendMessage]
  );

  // Save settings handler
  const handleSaveSettings = useCallback(
    (newSettings: AgentSettings) => {
      setAgentSettings(newSettings);
      sendMessage({
        type: "settings_update",
        settings: newSettings,
      });
    },
    [sendMessage]
  );

  // Tab configuration
  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "monitor", label: "Monitor", icon: "📹" },
    { id: "events", label: "Events", icon: "📋" },
    { id: "analytics", label: "Analytics", icon: "📊" },
    { id: "settings", label: "Settings", icon: "⚙️" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-mw-background text-mw-text-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-mw-surface-2 bg-mw-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold">
              <span className="text-mw-accent">Medi</span>Watch
            </h1>
            <StatusIndicator status={status} />
          </div>

          {/* Tab navigation */}
          <nav className="flex items-center gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-mw-accent/20 text-mw-accent"
                    : "text-mw-text-secondary hover:bg-mw-surface-2 hover:text-mw-text-primary"
                }`}
              >
                <span>{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </nav>

          {/* Active alert count */}
          {activeAlerts.length > 0 && (
            <button
              onClick={() => setActiveTab("monitor")}
              className="flex items-center gap-1.5 rounded-full bg-red-500/20 px-3 py-1 text-xs font-medium text-red-400 animate-pulse"
            >
              <span className="h-2 w-2 rounded-full bg-red-500" />
              {activeAlerts.length} Alert{activeAlerts.length > 1 ? "s" : ""}
            </button>
          )}
        </div>
      </header>

      {/* Disclaimer */}
      <div className="mx-auto w-full max-w-7xl px-4 pt-3">
        <DisclaimerBanner />
      </div>

      {/* Main Content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-4">
        {activeTab === "monitor" && (
          <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
            <LiveFeed status={status} metrics={metrics} />
            <AlertPanel
              alerts={activeAlerts}
              onAcknowledge={handleAcknowledge}
            />
          </div>
        )}

        {activeTab === "events" && <EventLog entries={eventLog} />}

        {activeTab === "analytics" && (
          <Analytics entries={eventLog} metrics={metrics} />
        )}

        {activeTab === "settings" && (
          <Settings settings={agentSettings} onSave={handleSaveSettings} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-mw-surface-2 px-4 py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between text-[10px] text-mw-text-secondary">
          <span>MediWatch v0.1.0 — AI-Assisted Patient Safety Monitoring</span>
          <span>Powered by Stream Vision Agents SDK + YOLO 11</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
