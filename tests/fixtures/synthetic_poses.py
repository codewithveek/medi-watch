"""
Synthetic pose data for testing MediWatch processor.

All data is synthetic — no patient data is ever used in tests.
Uses fixture data only, as required by AGENTS.md.

YOLO 11 Pose format: 17 keypoints, each [x, y, confidence]
Keypoint indices:
  0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
  5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
  9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
  13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle
"""

from __future__ import annotations


def generate_standing_pose() -> list[list[float]]:
    """Generate keypoints for a person standing upright."""
    return [
        [0.50, 0.10, 0.95],  # 0: nose
        [0.48, 0.08, 0.90],  # 1: left_eye
        [0.52, 0.08, 0.90],  # 2: right_eye
        [0.46, 0.10, 0.85],  # 3: left_ear
        [0.54, 0.10, 0.85],  # 4: right_ear
        [0.44, 0.25, 0.95],  # 5: left_shoulder
        [0.56, 0.25, 0.95],  # 6: right_shoulder
        [0.40, 0.40, 0.90],  # 7: left_elbow
        [0.60, 0.40, 0.90],  # 8: right_elbow
        [0.38, 0.50, 0.85],  # 9: left_wrist
        [0.62, 0.50, 0.85],  # 10: right_wrist
        [0.46, 0.55, 0.95],  # 11: left_hip
        [0.54, 0.55, 0.95],  # 12: right_hip
        [0.45, 0.75, 0.90],  # 13: left_knee
        [0.55, 0.75, 0.90],  # 14: right_knee
        [0.44, 0.95, 0.85],  # 15: left_ankle
        [0.56, 0.95, 0.85],  # 16: right_ankle
    ]


def generate_horizontal_pose() -> list[list[float]]:
    """Generate keypoints for a person lying horizontal (fallen)."""
    return [
        [0.15, 0.80, 0.90],  # 0: nose
        [0.13, 0.78, 0.85],  # 1: left_eye
        [0.17, 0.78, 0.85],  # 2: right_eye
        [0.11, 0.80, 0.80],  # 3: left_ear
        [0.19, 0.80, 0.80],  # 4: right_ear
        [0.25, 0.80, 0.90],  # 5: left_shoulder
        [0.25, 0.85, 0.90],  # 6: right_shoulder
        [0.35, 0.80, 0.85],  # 7: left_elbow
        [0.35, 0.85, 0.85],  # 8: right_elbow
        [0.45, 0.80, 0.80],  # 9: left_wrist
        [0.45, 0.85, 0.80],  # 10: right_wrist
        [0.55, 0.80, 0.90],  # 11: left_hip
        [0.55, 0.85, 0.90],  # 12: right_hip
        [0.70, 0.80, 0.85],  # 13: left_knee
        [0.70, 0.85, 0.85],  # 14: right_knee
        [0.85, 0.80, 0.80],  # 15: left_ankle
        [0.85, 0.85, 0.80],  # 16: right_ankle
    ]


def generate_arms_raised_pose() -> list[list[float]]:
    """Generate keypoints for a person with both arms raised (distress)."""
    return [
        [0.50, 0.10, 0.95],  # 0: nose
        [0.48, 0.08, 0.90],  # 1: left_eye
        [0.52, 0.08, 0.90],  # 2: right_eye
        [0.46, 0.10, 0.85],  # 3: left_ear
        [0.54, 0.10, 0.85],  # 4: right_ear
        [0.44, 0.25, 0.95],  # 5: left_shoulder
        [0.56, 0.25, 0.95],  # 6: right_shoulder
        [0.42, 0.15, 0.90],  # 7: left_elbow (raised)
        [0.58, 0.15, 0.90],  # 8: right_elbow (raised)
        [0.40, 0.05, 0.85],  # 9: left_wrist (above shoulder)
        [0.60, 0.05, 0.85],  # 10: right_wrist (above shoulder)
        [0.46, 0.55, 0.95],  # 11: left_hip
        [0.54, 0.55, 0.95],  # 12: right_hip
        [0.45, 0.75, 0.90],  # 13: left_knee
        [0.55, 0.75, 0.90],  # 14: right_knee
        [0.44, 0.95, 0.85],  # 15: left_ankle
        [0.56, 0.95, 0.85],  # 16: right_ankle
    ]


def generate_iv_interference_pose() -> list[list[float]]:
    """Generate keypoints for IV interference — hand near face/head."""
    return [
        [0.50, 0.10, 0.95],  # 0: nose
        [0.48, 0.08, 0.90],  # 1: left_eye
        [0.52, 0.08, 0.90],  # 2: right_eye
        [0.46, 0.10, 0.85],  # 3: left_ear
        [0.54, 0.10, 0.85],  # 4: right_ear
        [0.44, 0.25, 0.95],  # 5: left_shoulder
        [0.56, 0.25, 0.95],  # 6: right_shoulder
        [0.46, 0.18, 0.90],  # 7: left_elbow
        [0.60, 0.40, 0.90],  # 8: right_elbow
        [0.48, 0.11, 0.85],  # 9: left_wrist (near nose!)
        [0.62, 0.50, 0.85],  # 10: right_wrist
        [0.46, 0.55, 0.95],  # 11: left_hip
        [0.54, 0.55, 0.95],  # 12: right_hip
        [0.45, 0.75, 0.90],  # 13: left_knee
        [0.55, 0.75, 0.90],  # 14: right_knee
        [0.44, 0.95, 0.85],  # 15: left_ankle
        [0.56, 0.95, 0.85],  # 16: right_ankle
    ]


def generate_sitting_pose() -> list[list[float]]:
    """Generate keypoints for a person sitting (not falling, not distressed)."""
    return [
        [0.50, 0.20, 0.95],  # 0: nose
        [0.48, 0.18, 0.90],  # 1: left_eye
        [0.52, 0.18, 0.90],  # 2: right_eye
        [0.46, 0.20, 0.85],  # 3: left_ear
        [0.54, 0.20, 0.85],  # 4: right_ear
        [0.44, 0.35, 0.95],  # 5: left_shoulder
        [0.56, 0.35, 0.95],  # 6: right_shoulder
        [0.40, 0.50, 0.90],  # 7: left_elbow
        [0.60, 0.50, 0.90],  # 8: right_elbow
        [0.42, 0.55, 0.85],  # 9: left_wrist
        [0.58, 0.55, 0.85],  # 10: right_wrist
        [0.46, 0.60, 0.95],  # 11: left_hip
        [0.54, 0.60, 0.95],  # 12: right_hip
        [0.45, 0.75, 0.90],  # 13: left_knee
        [0.55, 0.75, 0.90],  # 14: right_knee
        [0.44, 0.90, 0.85],  # 15: left_ankle
        [0.56, 0.90, 0.85],  # 16: right_ankle
    ]
