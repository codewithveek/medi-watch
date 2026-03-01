"""Shared types and enums for MediWatch agent."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


class EventType(str, enum.Enum):
    """Detectable patient safety events."""

    FALL = "FALL"
    IMMOBILITY = "IMMOBILITY"
    DISTRESS = "DISTRESS"
    IV_INTERFERENCE = "IV_INTERFERENCE"


class Severity(str, enum.Enum):
    """Alert severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertChannel(str, enum.Enum):
    """Available alert dispatch channels."""

    DASHBOARD = "DASHBOARD"
    BROWSER_PUSH = "BROWSER_PUSH"
    VOICE = "VOICE"
    SMS = "SMS"
    CALL = "CALL"


class AgentStatus(str, enum.Enum):
    """Agent operational status."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


# --- Default severity mapping per event type ---
DEFAULT_SEVERITY: dict[EventType, Severity] = {
    EventType.FALL: Severity.HIGH,
    EventType.IMMOBILITY: Severity.MEDIUM,
    EventType.DISTRESS: Severity.HIGH,
    EventType.IV_INTERFERENCE: Severity.MEDIUM,
}

DISCLAIMER = "AI-Assisted Detection — Human Verification Required"


@dataclass
class FrameMetadata:
    """Metadata about the detection frame (no raw image data)."""

    pose_keypoints: list[list[float]]
    bounding_box: list[float]
    detection_zone: str = "patient_bed_area"


@dataclass
class AlertPayload:
    """Structured alert sent to dashboard and external channels."""

    event_type: EventType
    severity: Severity
    confidence: float
    detection_model: str
    description: str
    frame_metadata: FrameMetadata
    alert_channels: list[AlertChannel] = field(default_factory=list)
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    staff_note: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "eventType": self.event_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "detectionModel": self.detection_model,
            "description": self.description,
            "frameMetadata": {
                "poseKeypoints": self.frame_metadata.pose_keypoints,
                "boundingBox": self.frame_metadata.bounding_box,
                "detectionZone": self.frame_metadata.detection_zone,
            },
            "alertChannels": [ch.value for ch in self.alert_channels],
            "acknowledged": self.acknowledged,
            "acknowledgedAt": self.acknowledged_at,
            "acknowledgedBy": self.acknowledged_by,
            "staffNote": self.staff_note,
            "disclaimer": self.disclaimer,
        }


@dataclass
class AuditEntry:
    """Immutable audit log entry for every alert dispatch attempt."""

    alert_id: str
    timestamp: str
    channel: str
    status: str  # "sent" | "failed"
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dictionary."""
        return {
            "alertId": self.alert_id,
            "timestamp": self.timestamp,
            "channel": self.channel,
            "status": self.status,
            "error": self.error,
        }


@dataclass
class MetricsPayload:
    """System metrics sent periodically to the dashboard."""

    events_total: int = 0
    alerts_sent: int = 0
    alerts_acknowledged: int = 0
    avg_latency_ms: float = 0.0
    avg_ack_time_seconds: float = 0.0
    uptime_seconds: float = 0.0
    agent_status: str = AgentStatus.ONLINE.value
    active_model: str = "yolo11n-pose + gemini-2.5-flash"

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dictionary."""
        return {
            "eventsTotal": self.events_total,
            "alertsSent": self.alerts_sent,
            "alertsAcknowledged": self.alerts_acknowledged,
            "avgLatencyMs": self.avg_latency_ms,
            "avgAckTimeSeconds": self.avg_ack_time_seconds,
            "uptimeSeconds": self.uptime_seconds,
            "agentStatus": self.agent_status,
            "activeModel": self.active_model,
        }
