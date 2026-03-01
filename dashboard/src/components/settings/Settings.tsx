import React, { useState } from "react";
import type { AgentSettings } from "../../types/mediwatch";

interface SettingsProps {
  settings: AgentSettings;
  onSave: (settings: AgentSettings) => void;
}

/**
 * Settings panel with detection threshold sliders, channel toggles,
 * recipient configuration, and model selector.
 */
const Settings: React.FC<SettingsProps> = ({ settings: initial, onSave }) => {
  const [settings, setSettings] = useState<AgentSettings>({ ...initial });
  const [dirty, setDirty] = useState(false);

  const update = <K extends keyof AgentSettings>(
    key: K,
    value: AgentSettings[K]
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  };

  const handleSave = () => {
    onSave(settings);
    setDirty(false);
  };

  const handleReset = () => {
    setSettings({ ...initial });
    setDirty(false);
  };

  return (
    <div className="card flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-mw-text-primary">Settings</h2>
        {dirty && (
          <span className="text-[10px] text-orange-400">Unsaved changes</span>
        )}
      </div>

      {/* Detection Thresholds */}
      <section>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
          Detection Thresholds
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <ThresholdSlider
            label="Fall Confidence"
            value={settings.fallConfidenceThreshold}
            onChange={(v) => update("fallConfidenceThreshold", v)}
          />
          <ThresholdSlider
            label="Immobility Timeout (s)"
            value={settings.immobilityTimeoutSeconds}
            onChange={(v) => update("immobilityTimeoutSeconds", v)}
            min={30}
            max={600}
            step={10}
            format={(v) => `${v}s`}
          />
          <ThresholdSlider
            label="Distress Confidence"
            value={settings.distressConfidenceThreshold}
            onChange={(v) => update("distressConfidenceThreshold", v)}
          />
          <ThresholdSlider
            label="Cooldown Period (s)"
            value={settings.cooldownSeconds}
            onChange={(v) => update("cooldownSeconds", v)}
            min={5}
            max={120}
            step={5}
            format={(v) => `${v}s`}
          />
        </div>
      </section>

      {/* Alert Channels */}
      <section>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
          Alert Channels
        </h3>
        <div className="flex flex-wrap gap-4">
          <ChannelToggle
            label="Dashboard"
            enabled={settings.dashboardEnabled}
            onChange={(v) => update("dashboardEnabled", v)}
          />
          <ChannelToggle
            label="SMS (Twilio)"
            enabled={settings.smsEnabled}
            onChange={(v) => update("smsEnabled", v)}
          />
          <ChannelToggle
            label="Voice (Twilio)"
            enabled={settings.voiceEnabled}
            onChange={(v) => update("voiceEnabled", v)}
          />
          <ChannelToggle
            label="Voice (ElevenLabs)"
            enabled={settings.ttsEnabled}
            onChange={(v) => update("ttsEnabled", v)}
          />
        </div>
      </section>

      {/* Recipients */}
      <section>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
          Recipients
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <TextInput
            label="Nurse Phone"
            value={settings.nursePhone}
            onChange={(v) => update("nursePhone", v)}
            placeholder="+1234567890"
          />
          <TextInput
            label="Doctor Phone"
            value={settings.doctorPhone}
            onChange={(v) => update("doctorPhone", v)}
            placeholder="+1234567890"
          />
        </div>
      </section>

      {/* Model Selection */}
      <section>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-mw-text-secondary">
          Model Configuration
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wider text-mw-text-secondary">
              LLM Provider
            </label>
            <select
              value={settings.llmProvider}
              onChange={(e) =>
                update("llmProvider", e.target.value as "openai" | "gemini")
              }
              className="w-full rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2.5 py-1.5 text-xs text-mw-text-primary focus:border-mw-accent focus:outline-none"
            >
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="gemini">Google (Gemini Pro)</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] uppercase tracking-wider text-mw-text-secondary">
              Pose Model
            </label>
            <select
              value={settings.poseModel}
              onChange={(e) => update("poseModel", e.target.value)}
              className="w-full rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2.5 py-1.5 text-xs text-mw-text-primary focus:border-mw-accent focus:outline-none"
            >
              <option value="yolo11n-pose">YOLO 11n (Fast)</option>
              <option value="yolo11s-pose">YOLO 11s (Balanced)</option>
              <option value="yolo11m-pose">YOLO 11m (Accurate)</option>
            </select>
          </div>
        </div>
      </section>

      {/* Actions */}
      <div className="flex items-center gap-3 border-t border-mw-surface-2 pt-4">
        <button
          onClick={handleSave}
          disabled={!dirty}
          className="btn-primary text-xs disabled:opacity-50"
        >
          Save Settings
        </button>
        <button
          onClick={handleReset}
          disabled={!dirty}
          className="rounded-md bg-mw-surface-2 px-3 py-1.5 text-xs font-medium text-mw-text-secondary hover:text-mw-text-primary disabled:opacity-50 transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

/* ---------- Sub-components ---------- */

const ThresholdSlider: React.FC<{
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  format?: (v: number) => string;
}> = ({ label, value, onChange, min = 0, max = 1, step = 0.05, format }) => (
  <div>
    <div className="mb-1 flex items-center justify-between">
      <label className="text-[10px] uppercase tracking-wider text-mw-text-secondary">
        {label}
      </label>
      <span className="font-mono text-xs font-medium text-mw-text-primary">
        {format ? format(value) : `${(value * 100).toFixed(0)}%`}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-full accent-mw-accent"
    />
  </div>
);

const ChannelToggle: React.FC<{
  label: string;
  enabled: boolean;
  onChange: (v: boolean) => void;
}> = ({ label, enabled, onChange }) => (
  <label className="flex cursor-pointer items-center gap-2">
    <div
      className={`relative h-5 w-9 rounded-full transition-colors ${
        enabled ? "bg-mw-accent" : "bg-mw-surface-2"
      }`}
      onClick={() => onChange(!enabled)}
    >
      <div
        className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${
          enabled ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </div>
    <span className="text-xs text-mw-text-secondary">{label}</span>
  </label>
);

const TextInput: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}> = ({ label, value, onChange, placeholder }) => (
  <div>
    <label className="mb-1 block text-[10px] uppercase tracking-wider text-mw-text-secondary">
      {label}
    </label>
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-md border border-mw-surface-2 bg-mw-surface-2 px-2.5 py-1.5 text-xs text-mw-text-primary placeholder:text-mw-text-secondary/50 focus:border-mw-accent focus:outline-none"
    />
  </div>
);

export default Settings;
