"""
FastAPI + WebSocket server — Bridge between MediWatch agent and the dashboard.

Provides:
- WebSocket endpoint for real-time alert streaming + acknowledgments
- REST endpoints for health, metrics, audit log, and test alerts
- CORS configured for the Vite dev server
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agent.alerts import AlertDispatcher
from agent.config import Settings
from agent.processors import MediWatchProcessor
from agent.schemas import (
    AgentStatus,
    AlertPayload,
    EventType,
    FrameMetadata,
    MetricsPayload,
    Severity,
)

logger = logging.getLogger(__name__)

# --- Global state ---
settings = Settings()
processor = MediWatchProcessor(settings=settings)
dispatcher = AlertDispatcher(settings=settings)
connected_dashboards: list[WebSocket] = []

# Metrics tracking
_start_time = time.time()
_events_total = 0
_alerts_sent = 0
_alerts_acknowledged = 0
_ack_times: list[float] = []
_active_alerts: dict[str, AlertPayload] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — start metrics broadcast task."""
    task = asyncio.create_task(_metrics_broadcast_loop())
    logger.info("MediWatch agent server started on port %d", settings.agent_port)
    yield
    task.cancel()


app = FastAPI(
    title="MediWatch Agent API",
    description="Real-time patient safety monitoring agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for dashboard communication.

    Inbound: ACKNOWLEDGE, SETTINGS_UPDATE
    Outbound: ALERT, METRICS, AGENT_STATUS, ACK_CONFIRMED
    """
    await websocket.accept()
    connected_dashboards.append(websocket)
    logger.info("Dashboard connected (%d total)", len(connected_dashboards))

    # Send initial status
    await websocket.send_text(
        json.dumps(
            {
                "type": "AGENT_STATUS",
                "payload": {
                    "status": AgentStatus.ONLINE.value,
                    "activeModel": f"yolo11n-pose + {settings.active_llm}",
                    "uptime": time.time() - _start_time,
                },
            }
        )
    )

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "ACKNOWLEDGE":
                await _handle_acknowledgment(
                    alert_id=msg["alertId"],
                    staff_note=msg.get("staffNote"),
                    acknowledged_by=msg.get("acknowledgedBy", "staff"),
                )
            elif msg_type == "SETTINGS_UPDATE":
                await _handle_settings_update(msg.get("payload", {}))
            else:
                logger.warning("Unknown WebSocket message type: %s", msg_type)

    except WebSocketDisconnect:
        connected_dashboards.remove(websocket)
        logger.info("Dashboard disconnected (%d remaining)", len(connected_dashboards))
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        if websocket in connected_dashboards:
            connected_dashboards.remove(websocket)


# ---------------------------------------------------------------------------
# Broadcast helpers
# ---------------------------------------------------------------------------


async def broadcast_alert(alert_dict: dict) -> None:
    """Broadcast an alert payload to all connected dashboards."""
    payload = json.dumps({"type": "ALERT", "payload": alert_dict})
    disconnected: list[WebSocket] = []

    for ws in connected_dashboards:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        connected_dashboards.remove(ws)


async def broadcast_message(msg_type: str, payload: dict) -> None:
    """Broadcast a generic message to all connected dashboards."""
    message = json.dumps({"type": msg_type, "payload": payload})
    disconnected: list[WebSocket] = []

    for ws in connected_dashboards:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        connected_dashboards.remove(ws)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _handle_acknowledgment(
    alert_id: str,
    staff_note: str | None = None,
    acknowledged_by: str = "staff",
) -> None:
    """Handle alert acknowledgment from dashboard."""
    global _alerts_acknowledged

    alert = _active_alerts.get(alert_id)
    if alert:
        now = datetime.now(timezone.utc).isoformat()
        alert.acknowledged = True
        alert.acknowledged_at = now
        alert.acknowledged_by = acknowledged_by
        alert.staff_note = staff_note

        # Track ack time
        alert_time = datetime.fromisoformat(alert.timestamp)
        ack_time = datetime.fromisoformat(now)
        ack_seconds = (ack_time - alert_time).total_seconds()
        _ack_times.append(ack_seconds)
        _alerts_acknowledged += 1

        # Cancel any pending escalation
        dispatcher.cancel_escalation(alert_id)

        # Broadcast confirmation
        await broadcast_message(
            "ACK_CONFIRMED",
            {"alertId": alert_id, "acknowledgedAt": now, "acknowledgedBy": acknowledged_by},
        )

        logger.info("Alert %s acknowledged by %s (%.1fs)", alert_id, acknowledged_by, ack_seconds)
    else:
        logger.warning("Acknowledgment for unknown alert: %s", alert_id)


async def _handle_settings_update(payload: dict) -> None:
    """Handle real-time settings update from dashboard."""
    global settings

    for key, value in payload.items():
        # Convert camelCase to snake_case for Settings fields
        snake_key = _camel_to_snake(key)
        if hasattr(settings, snake_key):
            setattr(settings, snake_key, value)
            logger.info("Setting updated: %s = %s", snake_key, value)

    # Rebuild processor with new settings
    processor.settings = settings
    logger.info("Settings updated from dashboard")


def _camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


# ---------------------------------------------------------------------------
# Metrics broadcast loop
# ---------------------------------------------------------------------------


async def _metrics_broadcast_loop() -> None:
    """Broadcast system metrics to dashboards every 5 seconds."""
    while True:
        try:
            await asyncio.sleep(5)

            avg_ack = sum(_ack_times) / len(_ack_times) if _ack_times else 0.0

            metrics = MetricsPayload(
                events_total=_events_total,
                alerts_sent=_alerts_sent,
                alerts_acknowledged=_alerts_acknowledged,
                avg_ack_time_seconds=avg_ack,
                uptime_seconds=time.time() - _start_time,
                agent_status=AgentStatus.ONLINE.value,
                active_model=f"yolo11n-pose + {settings.active_llm}",
            )

            await broadcast_message("METRICS", metrics.to_dict())

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Metrics broadcast error: %s", e)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent": "mediwatch",
        "uptime_seconds": round(time.time() - _start_time, 1),
        "connected_dashboards": len(connected_dashboards),
    }


@app.get("/metrics")
async def metrics() -> dict:
    """Prometheus-compatible metrics for the dashboard analytics panel."""
    avg_ack = sum(_ack_times) / len(_ack_times) if _ack_times else 0.0
    return {
        "events_total": _events_total,
        "alerts_sent": _alerts_sent,
        "alerts_acknowledged": _alerts_acknowledged,
        "avg_ack_time_seconds": round(avg_ack, 1),
        "uptime_seconds": round(time.time() - _start_time, 1),
    }


@app.get("/audit-log")
async def audit_log() -> dict:
    """Return the full audit trail."""
    return {
        "count": len(dispatcher.audit_log),
        "entries": dispatcher.get_audit_log(),
    }


@app.get("/active-alerts")
async def active_alerts() -> dict:
    """Return all active (unacknowledged) alerts."""
    active = [a.to_dict() for a in _active_alerts.values() if not a.acknowledged]
    return {"count": len(active), "alerts": active}


@app.post("/test-alert")
async def test_alert(body: dict) -> dict:
    """
    Trigger a test alert manually for pipeline verification.

    Request body:
        {"eventType": "FALL", "confidence": 0.92}
    """
    global _events_total, _alerts_sent

    event_type_str = body.get("eventType", "FALL")
    confidence = body.get("confidence", 0.88)

    try:
        event_type = EventType(event_type_str)
    except ValueError:
        return {"error": f"Invalid event type: {event_type_str}"}

    severity_map = {
        EventType.FALL: Severity.HIGH,
        EventType.IMMOBILITY: Severity.MEDIUM,
        EventType.DISTRESS: Severity.HIGH,
        EventType.IV_INTERFERENCE: Severity.MEDIUM,
    }

    alert = AlertPayload(
        event_type=event_type,
        severity=severity_map.get(event_type, Severity.MEDIUM),
        confidence=confidence,
        detection_model=f"yolo11n-pose + {settings.active_llm}",
        description=(
            f"TEST ALERT: {event_type.value} detected. "
            f"Confidence: {confidence * 100:.0f}%. "
            f"Human verification required."
        ),
        frame_metadata=FrameMetadata(
            pose_keypoints=[[0.0, 0.0, 0.0]] * 17,
            bounding_box=[0.1, 0.2, 0.3, 0.4],
            detection_zone="test_zone",
        ),
    )

    _events_total += 1
    _active_alerts[alert.id] = alert

    # Dispatch
    entries = await dispatcher.dispatch(alert, broadcast_fn=broadcast_alert)
    _alerts_sent += len(entries)

    return {
        "status": "alert_triggered",
        "alert": alert.to_dict(),
        "audit_entries": [e.to_dict() for e in entries],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    uvicorn.run(
        "agent.server:app",
        host="0.0.0.0",
        port=settings.agent_port,
        reload=True,
        log_level="info",
    )
