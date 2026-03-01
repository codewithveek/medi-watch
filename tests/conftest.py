"""Shared test fixtures for MediWatch tests."""

from __future__ import annotations

import pytest

from agent.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    """
    Test settings with safe defaults.

    Never mock Settings with hardcoded values inline — always use this fixture.
    """
    return Settings(
        stream_api_key="test-stream-key",
        stream_api_secret="test-stream-secret",
        gemini_api_key="test-gemini-key",
        openai_api_key="test-openai-key",
        active_llm="gemini",
        elevenlabs_api_key="test-elevenlabs-key",
        deepgram_api_key="test-deepgram-key",
        twilio_account_sid="test-twilio-sid",
        twilio_auth_token="test-twilio-token",
        twilio_from_number="+15555555555",
        alert_phone_numbers="+15555555556",
        enable_voice_alerts=False,  # Disabled in tests — no external calls
        enable_sms_alerts=False,
        enable_call_alerts=False,
        enable_push_alerts=True,
        min_confidence=0.75,
        alert_cooldown_seconds=60,
        immobility_timeout_minutes=10,
        twilio_call_escalation_seconds=90,
        fall_critical_floor_seconds=30,
        immobility_critical_minutes=20,
        distress_repeat_window_seconds=300,
        yolo_model_path="weights/yolo11n-pose.pt",
        moondream_device="cpu",
        agent_port=8080,
        cors_origin="http://localhost:5173",
    )
