"""
Local camera capture + YOLO pose detection pipeline.

Captures frames from the system webcam, runs YOLO 11 Pose inference,
and yields (base64_frame, keypoints) tuples for the server to broadcast.

Raw frames NEVER leave this module as pixels — only base64-encoded JPEG
(for local dashboard display) and extracted keypoints (for processing).
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from agent.config import Settings

logger = logging.getLogger(__name__)


class CameraCapture:
    """
    Manages local webcam capture and YOLO pose estimation.

    Usage:
        camera = CameraCapture(settings)
        async for frame_b64, keypoints, annotated_b64 in camera.stream():
            # frame_b64: base64-encoded raw JPEG frame
            # keypoints: list of [x, y, confidence] per joint (17 joints) or None
            # annotated_b64: base64-encoded JPEG with YOLO skeleton overlay
            ...
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cap: cv2.VideoCapture | None = None
        self._model = None
        self._running = False
        self._paused = False

    def _init_camera(self) -> bool:
        """Open the webcam. Returns True on success."""
        idx = self.settings.camera_index
        cap = cv2.VideoCapture(idx)

        if not cap.isOpened():
            logger.error("Failed to open camera at index %d", idx)
            return False

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        cap.set(cv2.CAP_PROP_FPS, self.settings.camera_fps)

        # Minimize internal MSMF buffer to 1 frame so stale data
        # doesn't accumulate and cause grab-frame failures.
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Drain a few warm-up frames — MSMF often returns junk on the
        # first couple of reads after opening.
        for _ in range(5):
            cap.grab()

        self._cap = cap
        logger.info(
            "Camera opened: index=%d, resolution=%dx%d, target_fps=%d",
            idx,
            self.settings.camera_width,
            self.settings.camera_height,
            self.settings.camera_fps,
        )
        return True

    def _init_model(self) -> bool:
        """Load the YOLO pose model. Returns True on success."""
        model_path = self.settings.yolo_model_path

        try:
            from ultralytics import YOLO

            if Path(model_path).exists():
                self._model = YOLO(model_path)
                logger.info("YOLO model loaded from %s", model_path)
            else:
                # Download the default model if weights file doesn't exist
                logger.warning(
                    "Model file %s not found — downloading yolo11n-pose...",
                    model_path,
                )
                self._model = YOLO("yolo11n-pose.pt")
                logger.info("YOLO model downloaded and loaded")

            return True
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)
            return False

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode a BGR frame to base64 JPEG string."""
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.settings.frame_jpeg_quality]
        _, buffer = cv2.imencode(".jpg", frame, encode_params)
        return base64.b64encode(buffer).decode("utf-8")

    def _extract_keypoints(self, results) -> list[list[float]] | None:  # noqa: ANN001
        """
        Extract pose keypoints from YOLO results.

        Returns list of 17 [x, y, confidence] triples, or None if no person detected.
        """
        if not results or len(results) == 0:
            return None

        result = results[0]
        if result.keypoints is None or len(result.keypoints) == 0:
            return None

        # Take the first detected person
        kpts = result.keypoints[0]

        # kpts.data is shape (1, 17, 3) — [x, y, confidence]
        if kpts.data is not None and kpts.data.numel() > 0:
            data = kpts.data.cpu().numpy()
            if data.ndim == 3:
                data = data[0]  # (17, 3)
            return data.tolist()

        return None

    def _draw_overlay(
        self,
        frame: np.ndarray,
        results,  # noqa: ANN001
    ) -> np.ndarray:
        """Draw YOLO pose skeleton overlay on the frame."""
        if results and len(results) > 0:
            annotated = results[0].plot()
            return annotated
        return frame.copy()

    async def stream(self):
        """
        Async generator that yields (raw_b64, keypoints, annotated_b64) tuples.

        Runs the capture loop at the configured FPS. Uses asyncio.sleep
        to yield control between frames so the event loop stays responsive.
        """
        # Load the (potentially slow) YOLO model BEFORE opening the camera.
        # On Windows MSMF, opening the camera early causes buffer overflows
        # while the model is downloading / loading (~30-60s).
        if not self._init_model():
            logger.warning(
                "YOLO model failed to load — streaming raw frames without pose detection"
            )

        if not self._init_camera():
            logger.error("Camera initialization failed — stream will not start")
            return

        self._running = True
        frame_interval = 1.0 / self.settings.camera_fps
        frame_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 30  # Re-open camera after this many failures

        logger.info("Camera stream started (target %.0f FPS)", self.settings.camera_fps)

        try:
            while self._running:
                # If paused, still grab frames to keep the MSMF buffer
                # drained (prevents -1072875772 errors on resume) but
                # don't decode or yield them.
                if self._paused:
                    if self._cap is not None:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self._cap.grab,
                        )
                    await asyncio.sleep(frame_interval)
                    consecutive_failures = 0
                    continue

                loop_start = time.time()

                # Read frame in a thread to avoid blocking the event loop
                ret, frame = await asyncio.get_event_loop().run_in_executor(
                    None, self._cap.read  # type: ignore[union-attr]
                )

                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(
                            "Camera failed %d consecutive reads — re-opening...",
                            consecutive_failures,
                        )
                        await self._reopen_camera_async()
                        consecutive_failures = 0
                    await asyncio.sleep(0.1)
                    continue

                consecutive_failures = 0  # reset on success

                frame_count += 1
                keypoints: list[list[float]] | None = None
                annotated_b64: str | None = None

                # Run YOLO inference (in thread pool to avoid blocking)
                if self._model is not None:
                    results = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda f=frame: self._model.predict(  # type: ignore[union-attr]
                            f, verbose=False, conf=0.3
                        ),
                    )
                    keypoints = self._extract_keypoints(results)

                    # Draw overlay
                    annotated_frame = self._draw_overlay(frame, results)
                    annotated_b64 = self._encode_frame(annotated_frame)

                # Always encode the raw frame
                raw_b64 = self._encode_frame(frame)

                logger.debug(
                    "Frame %d | keypoints=%s",
                    frame_count,
                    keypoints is not None,
                )

                yield raw_b64, keypoints, annotated_b64 or raw_b64

                # Maintain target FPS
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Camera stream cancelled")
        except Exception as e:
            logger.error("Camera stream error: %s", e, exc_info=True)
        finally:
            self.stop()

    def pause(self) -> None:
        """Pause frame capture (camera stays open but stops reading)."""
        self._paused = True
        logger.info("Camera stream paused")

    def resume(self) -> None:
        """Resume frame capture."""
        self._paused = False
        logger.info("Camera stream resumed")

    @property
    def is_paused(self) -> bool:
        return self._paused

    def _reopen_camera(self) -> None:
        """Release and re-open the camera (recovers from MSMF failures)."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("Re-opening camera...")
        if not self._init_camera():
            logger.error("Camera re-open failed")

    async def _reopen_camera_async(self) -> None:
        """Release, wait for the driver to settle, and re-open the camera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

        # Give the MSMF driver time to fully release the device before
        # attempting to re-acquire it — avoids immediate re-open failures.
        logger.info("Re-opening camera (cooldown 2 s)...")
        await asyncio.sleep(2.0)

        if not self._init_camera():
            logger.error("Camera re-open failed")

    def stop(self) -> None:
        """Release the camera and stop streaming."""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released")
