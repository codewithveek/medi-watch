"""Shared types and enums for MediWatch agent."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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

    @classmethod
    def from_dict(cls, data: dict) -> AlertPayload:
        """Reconstruct an AlertPayload from a serialized dict."""
        fm = data.get("frameMetadata", {})
        return cls(
            event_type=EventType(data.get("eventType", data.get("event_type", "FALL"))),
            severity=Severity(data.get("severity", "MEDIUM")),
            confidence=data.get("confidence", 0.0),
            detection_model=data.get("detectionModel", data.get("detection_model", "")),
            description=data.get("description", ""),
            frame_metadata=FrameMetadata(
                pose_keypoints=fm.get("poseKeypoints", fm.get("pose_keypoints", [])),
                bounding_box=fm.get("boundingBox", fm.get("bounding_box", [])),
                detection_zone=fm.get("detectionZone", fm.get("detection_zone", "")),
            ),
            alert_channels=[
                AlertChannel(ch)
                for ch in data.get("alertChannels", data.get("alert_channels", []))
            ],
            acknowledged=data.get("acknowledged", False),
            acknowledged_at=data.get("acknowledgedAt", data.get("acknowledged_at")),
            acknowledged_by=data.get("acknowledgedBy", data.get("acknowledged_by")),
            staff_note=data.get("staffNote", data.get("staff_note")),
            id=data.get("id", str(uuid4())),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            disclaimer=data.get("disclaimer", DISCLAIMER),
        )


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
    fps: float = 0.0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dictionary."""
        return {
            "events_total": self.events_total,
            "alerts_sent": self.alerts_sent,
            "alerts_acknowledged": self.alerts_acknowledged,
            "avg_ack_time_seconds": self.avg_ack_time_seconds,
            "uptime_seconds": self.uptime_seconds,
            "agent_status": self.agent_status,
            "active_model": self.active_model,
            "fps": self.fps,
            "latency_ms": self.latency_ms,
            "events_detected": self.events_total,
            "active_alerts": 0,
        }
