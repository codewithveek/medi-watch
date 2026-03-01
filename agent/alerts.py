"""
AlertDispatcher — Multi-channel alert dispatch with mandatory audit logging.

Every dispatch attempt (success or failure) is logged to the audit trail.
This is not optional — it's a compliance requirement.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from agent.schemas import AlertChannel, AlertPayload, AuditEntry

if TYPE_CHECKING:
    from agent.config import Settings

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """
    Dispatches alerts to multiple channels and maintains an append-only audit log.

    Channels:
    - DASHBOARD: WebSocket broadcast (handled by server.py)
    - BROWSER_PUSH: Included in WebSocket payload (browser handles push)
    - VOICE: ElevenLabs TTS
    - SMS: Twilio SMS
    - CALL: Twilio voice call (escalation only)

    Every dispatch attempt is audited regardless of outcome.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.audit_log: list[AuditEntry] = []
        self._twilio_client = None
        self._pending_escalations: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]

    async def dispatch(
        self,
        alert: AlertPayload,
        *,
        broadcast_fn: object | None = None,
    ) -> list[AuditEntry]:
        """
        Dispatch an alert to all configured channels.

        Args:
            alert: The alert payload to dispatch.
            broadcast_fn: Async callable to broadcast via WebSocket.

        Returns:
            List of audit entries for this dispatch.
        """
        entries: list[AuditEntry] = []

        for channel in alert.alert_channels:
            entry = await self._dispatch_channel(alert, channel, broadcast_fn)
            entries.append(entry)
            self.audit_log.append(entry)

        # Schedule Twilio call escalation if enabled and Twilio is configured
        if (
            self.settings.enable_call_alerts
            and self._twilio_configured()
            and AlertChannel.CALL not in alert.alert_channels
            and not alert.acknowledged
        ):
            self._schedule_escalation(alert)

        logger.info(
            "Alert %s dispatched to %d channel(s)",
            alert.id,
            len(entries),
        )

        return entries

    async def _dispatch_channel(
        self,
        alert: AlertPayload,
        channel: AlertChannel,
        broadcast_fn: object | None = None,
    ) -> AuditEntry:
        """Dispatch to a single channel and return an audit entry."""
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            if channel == AlertChannel.DASHBOARD:
                await self._dispatch_dashboard(alert, broadcast_fn)
            elif channel == AlertChannel.BROWSER_PUSH:
                # Push notifications are handled client-side via WebSocket payload
                logger.info("Browser push included in WebSocket payload for alert %s", alert.id)
            elif channel == AlertChannel.VOICE:
                await self._dispatch_voice(alert)
            elif channel == AlertChannel.SMS:
                await self._dispatch_sms(alert)
            elif channel == AlertChannel.CALL:
                await self._dispatch_call(alert)

            entry = AuditEntry(
                alert_id=alert.id,
                timestamp=timestamp,
                channel=channel.value,
                status="sent",
            )
            logger.info("Alert %s sent via %s", alert.id, channel.value)

        except Exception as e:
            entry = AuditEntry(
                alert_id=alert.id,
                timestamp=timestamp,
                channel=channel.value,
                status="failed",
                error=str(e),
            )
            logger.error("Alert %s failed via %s: %s", alert.id, channel.value, e)

        return entry

    async def _dispatch_dashboard(
        self,
        alert: AlertPayload,
        broadcast_fn: object | None = None,
    ) -> None:
        """Send alert to connected dashboards via WebSocket."""
        if broadcast_fn and callable(broadcast_fn):
            await broadcast_fn(alert.to_dict())  # type: ignore[misc]

    async def _dispatch_voice(self, alert: AlertPayload) -> None:
        """Generate and play voice alert via ElevenLabs TTS."""
        if not self.settings.elevenlabs_api_key:
            logger.warning("ElevenLabs API key not configured — skipping voice alert")
            return

        try:
            from elevenlabs import AsyncElevenLabs

            client = AsyncElevenLabs(api_key=self.settings.elevenlabs_api_key)

            text = (
                f"Attention: {alert.event_type.value} detected. "
                f"{alert.description} "
                f"Severity: {alert.severity.value}. "
                f"This is an AI-assisted alert. Human verification required."
            )

            # Generate audio — convert() returns an async generator for streaming
            audio_chunks: list[bytes] = []
            async for chunk in client.text_to_speech.convert(
                text=text,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel — calm, professional
                model_id="eleven_turbo_v2_5",
            ):
                audio_chunks.append(chunk)

            logger.info("Voice alert generated for alert %s (%d chunks)", alert.id, len(audio_chunks))

        except ImportError:
            logger.warning("elevenlabs package not installed — skipping voice alert")
        except Exception as e:
            raise RuntimeError(f"ElevenLabs TTS failed: {e}") from e

    def _twilio_configured(self) -> bool:
        """Check whether all required Twilio credentials are present."""
        return bool(
            self.settings.twilio_account_sid
            and self.settings.twilio_auth_token
            and self.settings.twilio_from_number
            and self.settings.phone_numbers
        )

    async def _dispatch_sms(self, alert: AlertPayload) -> None:
        """Send SMS via Twilio to configured phone numbers."""
        if not self._twilio_configured():
            logger.warning("Twilio not fully configured — skipping SMS")
            return

        try:
            from twilio.rest import Client

            client = Client(
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token,
            )

            body = (
                f"⚠️ MediWatch Alert: {alert.event_type.value}\n"
                f"Severity: {alert.severity.value}\n"
                f"Confidence: {alert.confidence * 100:.0f}%\n"
                f"{alert.description}\n\n"
                f"AI-Assisted — Human Verification Required"
            )

            for number in self.settings.phone_numbers:
                message = client.messages.create(
                    body=body,
                    from_=self.settings.twilio_from_number,
                    to=number,
                )
                logger.info("SMS sent to %s: %s", number, message.sid)

        except ImportError:
            logger.warning("twilio package not installed — skipping SMS")
        except Exception as e:
            raise RuntimeError(f"Twilio SMS failed: {e}") from e

    async def _dispatch_call(self, alert: AlertPayload) -> None:
        """Make an automated call via Twilio for escalation."""
        if not self._twilio_configured():
            logger.warning("Twilio not fully configured — skipping call escalation")
            return

        try:
            from twilio.rest import Client

            client = Client(
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token,
            )

            twiml = (
                f"<Response><Say voice='alice'>"
                f"MediWatch Critical Alert. "
                f"{alert.event_type.value} detected with "
                f"{alert.severity.value} severity. "
                f"Confidence {alert.confidence * 100:.0f} percent. "
                f"This is an AI assisted alert. Human verification required immediately. "
                f"Please check the patient dashboard."
                f"</Say></Response>"
            )

            for number in self.settings.phone_numbers:
                call = client.calls.create(
                    twiml=twiml,
                    from_=self.settings.twilio_from_number,
                    to=number,
                )
                logger.info("Escalation call to %s: %s", number, call.sid)

        except ImportError:
            logger.warning("twilio package not installed — skipping call")
        except Exception as e:
            raise RuntimeError(f"Twilio call failed: {e}") from e

    def _schedule_escalation(self, alert: AlertPayload) -> None:
        """Schedule a Twilio call if alert is not acknowledged within threshold."""

        async def _escalation_task() -> None:
            await asyncio.sleep(self.settings.twilio_call_escalation_seconds)
            if not alert.acknowledged:
                logger.warning(
                    "Alert %s not acknowledged after %ds — escalating via call",
                    alert.id,
                    self.settings.twilio_call_escalation_seconds,
                )
                alert.alert_channels.append(AlertChannel.CALL)
                entry = await self._dispatch_channel(alert, AlertChannel.CALL)
                self.audit_log.append(entry)

        task = asyncio.create_task(_escalation_task())
        self._pending_escalations[alert.id] = task

    def cancel_escalation(self, alert_id: str) -> None:
        """Cancel a pending Twilio call escalation (alert was acknowledged)."""
        task = self._pending_escalations.pop(alert_id, None)
        if task and not task.done():
            task.cancel()
            logger.info("Escalation cancelled for alert %s", alert_id)

    def get_audit_log(self) -> list[dict]:
        """Return the full audit log as serializable dicts."""
        return [entry.to_dict() for entry in self.audit_log]
