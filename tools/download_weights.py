"""Download YOLO model weights for MediWatch."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"
MODEL_NAME = "yolo11n-pose.pt"


def download_weights() -> None:
    """Download YOLO 11 Nano Pose model weights using Ultralytics."""
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = WEIGHTS_DIR / MODEL_NAME

    if model_path.exists():
        logger.info("Weights already exist at %s", model_path)
        return

    logger.info("Downloading %s to %s ...", MODEL_NAME, WEIGHTS_DIR)

    try:
        from ultralytics import YOLO

        # Downloading a model by name triggers auto-download
        model = YOLO(MODEL_NAME)

        # Move the downloaded file to our weights directory
        import shutil

        default_path = Path(MODEL_NAME)
        if default_path.exists():
            shutil.move(str(default_path), str(model_path))
            logger.info("Weights saved to %s", model_path)
        else:
            logger.warning(
                "Model loaded but file not found at default location. "
                "Check Ultralytics cache directory."
            )

        # Verify
        _ = model.names
        logger.info("Model verified: %d classes", len(model.names))

    except ImportError:
        logger.error(
            "ultralytics not installed. Run: uv add 'ultralytics>=8.0'"
        )
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to download weights: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )
    download_weights()
