"""Unit tests for MediWatchProcessor — detection logic."""

from __future__ import annotations

import time

import pytest

from agent.processors import MediWatchProcessor
from tests.fixtures.synthetic_poses import (
    generate_arms_raised_pose,
    generate_horizontal_pose,
    generate_iv_interference_pose,
    generate_sitting_pose,
    generate_standing_pose,
)


class TestFallDetection:
    """Tests for fall detection logic."""

    def test_horizontal_pose_detected_as_fall(self, mock_settings):
        """A person lying horizontal should be detected as a fall."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_horizontal_pose()
        assert processor._is_fall(keypoints) is True

    def test_standing_pose_not_detected_as_fall(self, mock_settings):
        """A person standing upright should NOT be detected as a fall."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_standing_pose()
        assert processor._is_fall(keypoints) is False

    def test_sitting_pose_not_detected_as_fall(self, mock_settings):
        """A person sitting should NOT be detected as a fall."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_sitting_pose()
        assert processor._is_fall(keypoints) is False

    def test_fall_confidence_horizontal(self, mock_settings):
        """Fall confidence should be high for a horizontal person."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_horizontal_pose()
        confidence = processor._fall_confidence(keypoints)
        assert confidence >= 0.75

    def test_fall_confidence_standing(self, mock_settings):
        """Fall confidence should be low for a standing person."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_standing_pose()
        confidence = processor._fall_confidence(keypoints)
        assert confidence < 0.5


class TestCooldown:
    """Tests for cooldown / deduplication logic."""

    def test_cooldown_prevents_duplicate_alerts(self, mock_settings):
        """Same event type within cooldown period should be blocked."""
        processor = MediWatchProcessor(settings=mock_settings)
        processor.state.last_event_times["FALL"] = time.time()
        assert processor._not_in_cooldown("FALL") is False

    def test_cooldown_allows_after_expiry(self, mock_settings):
        """Event should be allowed after cooldown period expires."""
        processor = MediWatchProcessor(settings=mock_settings)
        # Set last event time to well beyond cooldown
        processor.state.last_event_times["FALL"] = time.time() - mock_settings.alert_cooldown_seconds - 1
        assert processor._not_in_cooldown("FALL") is True

    def test_different_event_types_have_separate_cooldowns(self, mock_settings):
        """Different event types should have independent cooldowns."""
        processor = MediWatchProcessor(settings=mock_settings)
        processor.state.last_event_times["FALL"] = time.time()
        assert processor._not_in_cooldown("IMMOBILITY") is True


class TestImmobility:
    """Tests for immobility detection."""

    def test_immobility_after_threshold(self, mock_settings):
        """Immobility should be detected after timeout threshold."""
        processor = MediWatchProcessor(settings=mock_settings)
        # Set last activity to well beyond timeout
        processor.state.last_active_time = time.time() - (mock_settings.immobility_timeout_minutes * 60 + 1)
        keypoints = generate_standing_pose()
        assert processor._is_immobile(keypoints) is True

    def test_no_immobility_when_recently_active(self, mock_settings):
        """No immobility if patient was recently active."""
        processor = MediWatchProcessor(settings=mock_settings)
        processor.state.last_active_time = time.time()
        keypoints = generate_standing_pose()
        assert processor._is_immobile(keypoints) is False


class TestDistress:
    """Tests for distress gesture detection."""

    def test_arms_raised_detected_as_distress(self, mock_settings):
        """Both arms raised should be detected as distress."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_arms_raised_pose()
        assert processor._is_distress(keypoints) is True

    def test_standing_not_distress(self, mock_settings):
        """Normal standing should NOT be detected as distress."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_standing_pose()
        assert processor._is_distress(keypoints) is False


class TestIVInterference:
    """Tests for IV/tube interference detection."""

    def test_hand_near_face_detected(self, mock_settings):
        """Hand near nose/face should be detected as IV interference."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_iv_interference_pose()
        assert processor._is_iv_interference(keypoints) is True

    def test_standing_not_iv_interference(self, mock_settings):
        """Normal standing should NOT be detected as IV interference."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_standing_pose()
        assert processor._is_iv_interference(keypoints) is False


class TestProcessIntegration:
    """Integration tests for the full process() pipeline."""

    @pytest.mark.asyncio
    async def test_fall_generates_alert(self, mock_settings):
        """Processing a fall pose should generate a FALL alert."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_horizontal_pose()
        result = await processor.process({"pose_keypoints": keypoints})
        assert result is not None
        assert len(result["detected_events"]) > 0
        assert result["detected_events"][0]["eventType"] == "FALL"

    @pytest.mark.asyncio
    async def test_standing_generates_no_alert(self, mock_settings):
        """Processing a standing pose should generate no alert."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_standing_pose()
        result = await processor.process({"pose_keypoints": keypoints})
        assert result is None

    @pytest.mark.asyncio
    async def test_no_keypoints_returns_none(self, mock_settings):
        """Processing empty data should return None."""
        processor = MediWatchProcessor(settings=mock_settings)
        result = await processor.process({})
        assert result is None

    @pytest.mark.asyncio
    async def test_alert_includes_confidence(self, mock_settings):
        """Every alert must include a confidence score."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_horizontal_pose()
        result = await processor.process({"pose_keypoints": keypoints})
        if result:
            for event in result["detected_events"]:
                assert "confidence" in event
                assert 0.0 <= event["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_alert_includes_disclaimer(self, mock_settings):
        """Every alert must include the disclaimer."""
        processor = MediWatchProcessor(settings=mock_settings)
        keypoints = generate_horizontal_pose()
        result = await processor.process({"pose_keypoints": keypoints})
        if result:
            for event in result["detected_events"]:
                assert "disclaimer" in event
                assert "Human Verification Required" in event["disclaimer"]
