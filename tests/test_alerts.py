"""Unit tests for AlertDispatcher — audit logging and channel dispatch."""

from __future__ import annotations

import pytest

from agent.alerts import AlertDispatcher
from agent.types import AlertChannel, AlertPayload, FrameMetadata, EventType, Severity


def _make_test_alert(channels: list[AlertChannel] | None = None) -> AlertPayload:
    """Create a test alert payload. Uses synthetic data only."""
    return AlertPayload(
        event_type=EventType.FALL,
        severity=Severity.HIGH,
        confidence=0.88,
        detection_model="yolo11n-pose + gemini",
        description="TEST: Fall detected. Confidence: 88%. Human verification required.",
        frame_metadata=FrameMetadata(
            pose_keypoints=[[0.0, 0.0, 0.0]] * 17,
            bounding_box=[0.1, 0.2, 0.3, 0.4],
            detection_zone="test_zone",
        ),
        alert_channels=channels or [AlertChannel.DASHBOARD, AlertChannel.BROWSER_PUSH],
    )


class TestAuditLogging:
    """Audit trail is mandatory — every dispatch must be logged."""

    @pytest.mark.asyncio
    async def test_every_dispatch_produces_audit_entry(self, mock_settings):
        """Every channel dispatch must produce an audit entry."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        alert = _make_test_alert()

        entries = await dispatcher.dispatch(alert)

        assert len(entries) == len(alert.alert_channels)
        for entry in entries:
            assert entry.alert_id == alert.id
            assert entry.status in ("sent", "failed")
            assert entry.channel in [ch.value for ch in AlertChannel]

    @pytest.mark.asyncio
    async def test_audit_log_is_append_only(self, mock_settings):
        """Audit log must grow with each dispatch — never shrink."""
        dispatcher = AlertDispatcher(settings=mock_settings)

        alert1 = _make_test_alert()
        await dispatcher.dispatch(alert1)
        count_after_first = len(dispatcher.audit_log)

        alert2 = _make_test_alert()
        await dispatcher.dispatch(alert2)
        count_after_second = len(dispatcher.audit_log)

        assert count_after_second > count_after_first

    @pytest.mark.asyncio
    async def test_failed_dispatch_still_logged(self, mock_settings):
        """Even failed dispatches must produce an audit entry."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        alert = _make_test_alert(channels=[AlertChannel.VOICE])

        # Voice will fail because elevenlabs is not actually configured
        entries = await dispatcher.dispatch(alert)

        assert len(entries) == 1
        # Should be "sent" (logged as sent since no actual API call with disabled flag)
        assert entries[0].status in ("sent", "failed")

    @pytest.mark.asyncio
    async def test_audit_log_serialization(self, mock_settings):
        """Audit log must be serializable to dict."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        alert = _make_test_alert()

        await dispatcher.dispatch(alert)

        log = dispatcher.get_audit_log()
        assert isinstance(log, list)
        assert len(log) > 0
        for entry in log:
            assert "alertId" in entry
            assert "timestamp" in entry
            assert "channel" in entry
            assert "status" in entry


class TestChannelDispatch:
    """Test individual channel dispatch behavior."""

    @pytest.mark.asyncio
    async def test_dashboard_dispatch_calls_broadcast(self, mock_settings):
        """Dashboard channel should call the broadcast function."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        alert = _make_test_alert(channels=[AlertChannel.DASHBOARD])

        broadcast_called = False
        received_payload = None

        async def mock_broadcast(payload):
            nonlocal broadcast_called, received_payload
            broadcast_called = True
            received_payload = payload

        await dispatcher.dispatch(alert, broadcast_fn=mock_broadcast)

        assert broadcast_called
        assert received_payload is not None
        assert received_payload["eventType"] == "FALL"

    @pytest.mark.asyncio
    async def test_browser_push_logged(self, mock_settings):
        """Browser push channel should be logged in audit."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        alert = _make_test_alert(channels=[AlertChannel.BROWSER_PUSH])

        entries = await dispatcher.dispatch(alert)
        assert len(entries) == 1
        assert entries[0].channel == "BROWSER_PUSH"
        assert entries[0].status == "sent"


class TestEscalation:
    """Test Twilio call escalation mechanics."""

    def test_cancel_escalation(self, mock_settings):
        """Cancelling escalation for unknown alert should not raise."""
        dispatcher = AlertDispatcher(settings=mock_settings)
        dispatcher.cancel_escalation("nonexistent-id")  # Should not raise
