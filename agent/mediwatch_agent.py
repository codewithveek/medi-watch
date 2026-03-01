"""
MediWatch Agent — Vision Agents SDK entrypoint.

Combines local vision models (YOLO, Moondream) with cloud LLM reasoning
(Gemini / OpenAI) to detect patient safety events and dispatch alerts.

Note: This uses the correct import paths from vision_agents SDK:
- vision_agents.core for Agent, User
- vision_agents.plugins for integrations (getstream, gemini, openai, etc.)
"""

from __future__ import annotations

import logging
import pathlib

from agent.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()

INSTRUCTIONS_PATH = pathlib.Path(__file__).parent / "instructions" / "mediwatch_protocol.md"


def build_agent():  # type: ignore[no-untyped-def]
    """
    Build and return the MediWatch agent using Vision Agents SDK.

    The agent combines:
    - YOLO 11 Pose for skeleton/keypoint detection (local)
    - MediWatchProcessor for event classification (local)
    - Gemini or OpenAI for contextual reasoning (cloud)
    - ElevenLabs for voice alerts (cloud)
    - Deepgram for voice acknowledgment (cloud)

    Raw video frames NEVER leave the local machine.
    """
    try:
        from vision_agents.core import Agent, User
        from vision_agents.plugins import deepgram, elevenlabs, getstream
    except ImportError as e:
        logger.error(
            "Vision Agents SDK not installed. Run: uv add "
            '"vision-agents[getstream,openai,elevenlabs,deepgram]"'
        )
        raise SystemExit(1) from e

    # Select LLM based on config
    llm = _build_llm()

    # Load instructions
    instructions = _load_instructions()

    # Build YOLO processor
    yolo_processor = _build_yolo_processor()

    # Build custom MediWatch processor
    from agent.processors import MediWatchProcessor

    mediwatch_processor = MediWatchProcessor(settings=settings)

    processors = []
    if yolo_processor:
        processors.append(yolo_processor)
    processors.append(mediwatch_processor)

    agent = Agent(
        edge=getstream.Edge(),
        agent_user=User(name="MediWatch", id="mediwatch-agent"),
        instructions=instructions,
        processors=processors,
        llm=llm,
        tts=elevenlabs.TTS(voice_id="21m00Tcm4TlvDq8ikWAM"),
        stt=deepgram.STT(model="nova-3"),
    )

    logger.info("MediWatch agent built successfully (LLM: %s)", settings.active_llm)
    return agent


def _build_llm():  # type: ignore[no-untyped-def]
    """Build the LLM integration based on settings."""
    if settings.active_llm == "gemini":
        try:
            from vision_agents.plugins import gemini

            return gemini.LLM("gemini-2.5-flash")
        except ImportError:
            logger.warning("Gemini plugin not available, falling back to OpenAI")

    try:
        from vision_agents.plugins import openai

        return openai.LLM("gpt-4o")
    except ImportError:
        logger.error("No LLM plugin available — agent will run in local-only mode")
        return None


def _build_yolo_processor():  # type: ignore[no-untyped-def]
    """Build the YOLO pose processor if weights are available."""
    try:
        from vision_agents.plugins.ultralytics import YOLOPoseProcessor

        model_path = pathlib.Path(settings.yolo_model_path)
        if model_path.exists():
            return YOLOPoseProcessor(
                model_path=str(model_path),
                device=settings.moondream_device,
            )
        else:
            logger.warning(
                "YOLO weights not found at %s — run: uv run python tools/download_weights.py",
                model_path,
            )
            return None

    except ImportError:
        logger.warning("Ultralytics plugin not available — YOLO processor disabled")
        return None


def _load_instructions() -> str:
    """Load agent instructions from file, with fallback to inline."""
    if INSTRUCTIONS_PATH.exists():
        return f"Read @{INSTRUCTIONS_PATH}"

    # Fallback inline instructions
    return """
You are MediWatch, a patient safety monitoring assistant.

You receive structured event data from local vision models (YOLO pose detection
and Moondream scene analysis). Your role is to:

1. Reason about whether the detected event is a genuine safety concern
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Generate a clear, concise, plain-English alert description for nursing staff
4. Never make diagnostic claims — describe observations only
5. Always include uncertainty when confidence is below 0.85

You never see raw video. You receive pose keypoints and scene descriptors only.
Format your response as structured JSON matching the AlertPayload schema.

Always include these phrases:
- "Human verification required"
- "AI-Assisted — Not Diagnostic"
- Confidence score disclosure
"""


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    agent = build_agent()
    logger.info("Agent ready. Use 'uv run python agent/server.py' to start the server.")
