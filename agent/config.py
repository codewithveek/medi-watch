"""Pydantic-based settings for MediWatch. All configuration is env-driven."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central configuration for MediWatch agent.

    All values are loaded from environment variables (or .env file).
    Never access os.environ directly — always use this Settings object.
    """

    # --- Stream ---
    stream_api_key: str = ""
    stream_api_secret: str = ""

    # --- LLM (primary: Gemini, fallback: OpenAI) ---
    gemini_api_key: str = ""
    openai_api_key: str = ""
    active_llm: str = "gemini"  # "gemini" | "openai"

    # --- Alert channels ---
    elevenlabs_api_key: str = ""
    deepgram_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    alert_phone_numbers: list[str] = []

    # --- Channel toggles ---
    enable_voice_alerts: bool = True
    enable_sms_alerts: bool = True
    enable_call_alerts: bool = True
    enable_push_alerts: bool = True

    # --- Detection thresholds (configurable, never hardcoded) ---
    min_confidence: float = 0.75
    alert_cooldown_seconds: int = 60
    immobility_timeout_minutes: int = 10
    twilio_call_escalation_seconds: int = 90

    # --- Severity escalation thresholds ---
    fall_critical_floor_seconds: int = 30
    immobility_critical_minutes: int = 20
    distress_repeat_window_seconds: int = 300

    # --- Model paths ---
    yolo_model_path: str = "weights/yolo11n-pose.pt"
    moondream_device: str = "cuda"  # "cuda" | "cpu"

    # --- Server ---
    agent_port: int = 8080
    cors_origin: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
