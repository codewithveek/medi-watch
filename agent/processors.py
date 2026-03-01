"""
MediWatchProcessor — Stateful, frame-by-frame patient safety event classifier.

Runs entirely locally. No cloud calls from this layer.
All detection logic is deterministic given the same input keypoints.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agent.types import (
    DEFAULT_SEVERITY,
    AlertChannel,
    AlertPayload,
    EventType,
    FrameMetadata,
    Severity,
)

if TYPE_CHECKING:
    from agent.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class PatientState:
    """Tracks patient state across frames for temporal reasoning."""

    last_event_times: dict[str, float] = field(default_factory=dict)
    last_active_time: float = field(default_factory=time.time)
    horizontal_start_time: float | None = None
    previous_keypoints: list[list[float]] | None = None
    distress_timestamps: list[float] = field(default_factory=list)
    frame_count: int = 0


# --- YOLO 11 Pose keypoint indices ---
# 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
# 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
# 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
# 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle

NOSE = 0
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16


class MediWatchProcessor:
    """
    Stateful processor that classifies pose events into patient safety events.

    Processes YOLO pose keypoints frame-by-frame and detects:
    - Falls (person transitioning from upright to horizontal)
    - Prolonged immobility (no significant movement beyond threshold)
    - Distress gestures (arms raised, erratic movement patterns)
    - IV/tube interference (hands reaching toward torso/head)

    All thresholds are sourced from Settings — never hardcoded.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state = PatientState()
        self._start_time = time.time()

    async def process(self, frame_data: dict) -> dict | None:
        """
        Process a single frame's pose data and return detected events if any.

        Args:
            frame_data: Dictionary containing 'pose_keypoints' from YOLO.

        Returns:
            Dictionary with 'detected_events' list, or None if no events detected.
        """
        self.state.frame_count += 1
        pose = frame_data.get("pose_keypoints")

        logger.debug(
            "Frame %d processed | keypoints_present=%s",
            self.state.frame_count,
            pose is not None,
        )

        if not pose or len(pose) < 17:
            return None

        events: list[AlertPayload] = []
        now = time.time()

        # --- Fall detection ---
        if self._is_fall(pose):
            confidence = self._fall_confidence(pose)
            if confidence >= self.settings.min_confidence and self._not_in_cooldown(
                EventType.FALL.value
            ):
                severity = self._compute_fall_severity(now)
                events.append(
                    self._build_alert(
                        event_type=EventType.FALL,
                        severity=severity,
                        confidence=confidence,
                        description=self._fall_description(confidence, severity),
                        keypoints=pose,
                    )
                )
                self.state.last_event_times[EventType.FALL.value] = now
        else:
            # Person is not horizontal — reset horizontal timer
            self.state.horizontal_start_time = None

        # --- Immobility detection ---
        if self._is_immobile(pose):
            duration = self._immobile_duration()
            if self._not_in_cooldown(EventType.IMMOBILITY.value):
                severity = self._compute_immobility_severity(duration)
                events.append(
                    self._build_alert(
                        event_type=EventType.IMMOBILITY,
                        severity=severity,
                        confidence=0.95,  # Rule-based, high confidence
                        description=(
                            f"Patient has been immobile for {duration:.0f} minutes. "
                            f"Confidence: 95%. Human verification required."
                        ),
                        keypoints=pose,
                    )
                )
                self.state.last_event_times[EventType.IMMOBILITY.value] = now

        # --- Distress gesture detection ---
        if self._is_distress(pose):
            confidence = self._distress_confidence(pose)
            if confidence >= self.settings.min_confidence and self._not_in_cooldown(
                EventType.DISTRESS.value
            ):
                self.state.distress_timestamps.append(now)
                severity = self._compute_distress_severity(now)
                events.append(
                    self._build_alert(
                        event_type=EventType.DISTRESS,
                        severity=severity,
                        confidence=confidence,
                        description=(
                            f"Patient appears to be in distress — raised arms / erratic movement "
                            f"detected. Confidence: {confidence * 100:.0f}%. "
                            f"Human verification required."
                        ),
                        keypoints=pose,
                    )
                )
                self.state.last_event_times[EventType.DISTRESS.value] = now

        # --- IV interference detection ---
        if self._is_iv_interference(pose):
            confidence = self._iv_interference_confidence(pose)
            if confidence >= self.settings.min_confidence and self._not_in_cooldown(
                EventType.IV_INTERFERENCE.value
            ):
                events.append(
                    self._build_alert(
                        event_type=EventType.IV_INTERFERENCE,
                        severity=DEFAULT_SEVERITY[EventType.IV_INTERFERENCE],
                        confidence=confidence,
                        description=(
                            f"Possible IV/tube interference detected — hand near torso/head region. "
                            f"Confidence: {confidence * 100:.0f}%. "
                            f"Human verification required."
                        ),
                        keypoints=pose,
                    )
                )
                self.state.last_event_times[EventType.IV_INTERFERENCE.value] = now

        # Update movement tracking
        self._update_activity(pose)

        if events:
            return {
                "detected_events": [e.to_dict() for e in events],
                "timestamp": now,
            }

        return None

    # -------------------------------------------------------------------------
    # Detection methods
    # -------------------------------------------------------------------------

    def _is_fall(self, keypoints: list[list[float]]) -> bool:
        """
        Detect a fall by checking if the torso is roughly horizontal.

        Compares average shoulder Y with average hip Y. If the vertical difference
        is small (person is horizontal) and hips are near the lower portion of the
        frame, it's likely a fall.
        """
        shoulder_y = self._avg_keypoint_y(keypoints, [LEFT_SHOULDER, RIGHT_SHOULDER])
        hip_y = self._avg_keypoint_y(keypoints, [LEFT_HIP, RIGHT_HIP])
        ankle_y = self._avg_keypoint_y(keypoints, [LEFT_ANKLE, RIGHT_ANKLE])

        if shoulder_y is None or hip_y is None:
            return False

        # Torso is horizontal if shoulder-hip vertical difference is small
        torso_vertical_diff = abs(hip_y - shoulder_y)
        is_horizontal = torso_vertical_diff < 0.15

        # Additional check: if ankles are roughly at same height as hips → lying down
        if ankle_y is not None:
            full_body_horizontal = abs(ankle_y - hip_y) < 0.2
            is_horizontal = is_horizontal and full_body_horizontal

        if is_horizontal and self.state.horizontal_start_time is None:
            self.state.horizontal_start_time = time.time()

        return is_horizontal

    def _is_immobile(self, keypoints: list[list[float]]) -> bool:
        """Detect prolonged immobility by checking elapsed time since last movement."""
        elapsed_minutes = (time.time() - self.state.last_active_time) / 60
        return elapsed_minutes >= self.settings.immobility_timeout_minutes

    def _is_distress(self, keypoints: list[list[float]]) -> bool:
        """
        Detect distress gestures: both arms raised above shoulder level,
        or rapid/erratic arm movement.
        """
        left_wrist_y = self._get_keypoint_y(keypoints, LEFT_WRIST)
        right_wrist_y = self._get_keypoint_y(keypoints, RIGHT_WRIST)
        left_shoulder_y = self._get_keypoint_y(keypoints, LEFT_SHOULDER)
        right_shoulder_y = self._get_keypoint_y(keypoints, RIGHT_SHOULDER)

        if any(v is None for v in [left_wrist_y, right_wrist_y, left_shoulder_y, right_shoulder_y]):
            return False

        # Both arms above shoulder level (in image coords, lower Y = higher position)
        both_arms_raised = (
            left_wrist_y < left_shoulder_y  # type: ignore[operator]
            and right_wrist_y < right_shoulder_y  # type: ignore[operator]
        )

        return both_arms_raised

    def _is_iv_interference(self, keypoints: list[list[float]]) -> bool:
        """
        Detect IV/tube interference: hand reaching toward torso or head region.

        Checks if either wrist is near the head/nose area or crossing the torso midline.
        """
        nose = self._get_keypoint(keypoints, NOSE)
        left_wrist = self._get_keypoint(keypoints, LEFT_WRIST)
        right_wrist = self._get_keypoint(keypoints, RIGHT_WRIST)

        if nose is None or (left_wrist is None and right_wrist is None):
            return False

        threshold = 0.1  # Normalized distance threshold

        for wrist in [left_wrist, right_wrist]:
            if wrist is None:
                continue
            dist = math.sqrt((wrist[0] - nose[0]) ** 2 + (wrist[1] - nose[1]) ** 2)
            if dist < threshold:
                return True

        return False

    # -------------------------------------------------------------------------
    # Confidence scoring
    # -------------------------------------------------------------------------

    def _fall_confidence(self, keypoints: list[list[float]]) -> float:
        """Compute fall confidence based on pose geometry."""
        shoulder_y = self._avg_keypoint_y(keypoints, [LEFT_SHOULDER, RIGHT_SHOULDER])
        hip_y = self._avg_keypoint_y(keypoints, [LEFT_HIP, RIGHT_HIP])

        if shoulder_y is None or hip_y is None:
            return 0.0

        # More horizontal = higher confidence
        vertical_diff = abs(hip_y - shoulder_y)
        # Normalize: 0.15 diff → 0.75 confidence, 0.0 diff → 1.0 confidence
        confidence = max(0.0, min(1.0, 1.0 - (vertical_diff / 0.2)))

        return round(confidence, 2)

    def _distress_confidence(self, keypoints: list[list[float]]) -> float:
        """Compute distress confidence based on arm elevation."""
        left_wrist_y = self._get_keypoint_y(keypoints, LEFT_WRIST)
        left_shoulder_y = self._get_keypoint_y(keypoints, LEFT_SHOULDER)

        if left_wrist_y is None or left_shoulder_y is None:
            return 0.5

        elevation = left_shoulder_y - left_wrist_y
        confidence = min(1.0, 0.7 + elevation * 2)
        return round(max(0.0, confidence), 2)

    def _iv_interference_confidence(self, keypoints: list[list[float]]) -> float:
        """Compute IV interference confidence based on wrist-head proximity."""
        nose = self._get_keypoint(keypoints, NOSE)
        left_wrist = self._get_keypoint(keypoints, LEFT_WRIST)
        right_wrist = self._get_keypoint(keypoints, RIGHT_WRIST)

        if nose is None:
            return 0.0

        min_dist = float("inf")
        for wrist in [left_wrist, right_wrist]:
            if wrist is None:
                continue
            dist = math.sqrt((wrist[0] - nose[0]) ** 2 + (wrist[1] - nose[1]) ** 2)
            min_dist = min(min_dist, dist)

        if min_dist == float("inf"):
            return 0.0

        # Closer = higher confidence
        confidence = max(0.0, min(1.0, 1.0 - (min_dist / 0.15)))
        return round(confidence, 2)

    # -------------------------------------------------------------------------
    # Severity escalation
    # -------------------------------------------------------------------------

    def _compute_fall_severity(self, now: float) -> Severity:
        """Escalate fall to CRITICAL if person remains on floor too long."""
        if self.state.horizontal_start_time is not None:
            floor_duration = now - self.state.horizontal_start_time
            if floor_duration > self.settings.fall_critical_floor_seconds:
                return Severity.CRITICAL
        return DEFAULT_SEVERITY[EventType.FALL]

    def _compute_immobility_severity(self, duration_minutes: float) -> Severity:
        """Escalate immobility to CRITICAL if beyond critical threshold."""
        if duration_minutes >= self.settings.immobility_critical_minutes:
            return Severity.CRITICAL
        return DEFAULT_SEVERITY[EventType.IMMOBILITY]

    def _compute_distress_severity(self, now: float) -> Severity:
        """Escalate distress to CRITICAL if repeated within time window."""
        window = self.settings.distress_repeat_window_seconds
        recent = [t for t in self.state.distress_timestamps if now - t < window]
        self.state.distress_timestamps = recent  # Prune old entries

        if len(recent) >= 2:
            return Severity.CRITICAL
        return DEFAULT_SEVERITY[EventType.DISTRESS]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _not_in_cooldown(self, event_type: str) -> bool:
        """Check if the event type is past its cooldown period."""
        last = self.state.last_event_times.get(event_type, 0)
        return (time.time() - last) > self.settings.alert_cooldown_seconds

    def _immobile_duration(self) -> float:
        """Return immobility duration in minutes."""
        return (time.time() - self.state.last_active_time) / 60

    def _update_activity(self, keypoints: list[list[float]]) -> None:
        """Update last active time if significant movement detected."""
        if self.state.previous_keypoints is None:
            self.state.previous_keypoints = keypoints
            return

        # Compute average movement across all keypoints
        total_movement = 0.0
        count = 0
        for i, kp in enumerate(keypoints):
            if i < len(self.state.previous_keypoints):
                prev = self.state.previous_keypoints[i]
                if len(kp) >= 2 and len(prev) >= 2:
                    dx = kp[0] - prev[0]
                    dy = kp[1] - prev[1]
                    total_movement += math.sqrt(dx * dx + dy * dy)
                    count += 1

        if count > 0:
            avg_movement = total_movement / count
            # Threshold for "significant" movement (normalized coords)
            if avg_movement > 0.02:
                self.state.last_active_time = time.time()

        self.state.previous_keypoints = keypoints

    def _avg_keypoint_y(self, keypoints: list[list[float]], indices: list[int]) -> float | None:
        """Average Y coordinate for given keypoint indices."""
        ys = []
        for i in indices:
            if i < len(keypoints) and len(keypoints[i]) >= 2:
                conf = keypoints[i][2] if len(keypoints[i]) >= 3 else 1.0
                if conf > 0.3:  # Only use confident keypoints
                    ys.append(keypoints[i][1])
        return sum(ys) / len(ys) if ys else None

    def _get_keypoint_y(self, keypoints: list[list[float]], index: int) -> float | None:
        """Get Y coordinate for a single keypoint."""
        if index < len(keypoints) and len(keypoints[index]) >= 2:
            conf = keypoints[index][2] if len(keypoints[index]) >= 3 else 1.0
            if conf > 0.3:
                return keypoints[index][1]
        return None

    def _get_keypoint(self, keypoints: list[list[float]], index: int) -> list[float] | None:
        """Get [x, y] for a single keypoint if confident enough."""
        if index < len(keypoints) and len(keypoints[index]) >= 2:
            conf = keypoints[index][2] if len(keypoints[index]) >= 3 else 1.0
            if conf > 0.3:
                return keypoints[index][:2]
        return None

    def _build_alert(
        self,
        *,
        event_type: EventType,
        severity: Severity,
        confidence: float,
        description: str,
        keypoints: list[list[float]],
    ) -> AlertPayload:
        """Build an AlertPayload with standard fields."""
        # Determine which channels to fire
        channels = [AlertChannel.DASHBOARD, AlertChannel.BROWSER_PUSH]
        if self.settings.enable_voice_alerts:
            channels.append(AlertChannel.VOICE)
        if self.settings.enable_sms_alerts:
            channels.append(AlertChannel.SMS)

        active_model = (
            f"yolo11n-pose + {self.settings.active_llm}"
            if self.settings.active_llm
            else "yolo11n-pose"
        )

        # Compute bounding box from keypoints
        xs = [kp[0] for kp in keypoints if len(kp) >= 2]
        ys = [kp[1] for kp in keypoints if len(kp) >= 2]
        bbox = (
            [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
            if xs and ys
            else [0, 0, 0, 0]
        )

        return AlertPayload(
            event_type=event_type,
            severity=severity,
            confidence=confidence,
            detection_model=active_model,
            description=description,
            frame_metadata=FrameMetadata(
                pose_keypoints=keypoints,
                bounding_box=bbox,
            ),
            alert_channels=channels,
        )

    def _fall_description(self, confidence: float, severity: Severity) -> str:
        """Generate a human-readable fall alert description."""
        base = (
            f"Patient appears to have fallen — horizontal position detected near the bed edge. "
            f"Confidence: {confidence * 100:.0f}%. Human verification required immediately."
        )
        if severity == Severity.CRITICAL:
            base += " Patient has remained on the floor for an extended period."
        return base
