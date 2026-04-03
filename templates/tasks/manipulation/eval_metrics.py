#!/usr/bin/env python3
"""Compute detailed quality metrics for manipulation tasks during evaluation.

Stub template — the Metric Design Agent customizes per project.
"""

import re
from pathlib import Path

import numpy as np


def parse_tier2_config(config_path):
    """Parse Tier 2 Normalization from monitor_config.md."""
    if config_path is None:
        return None
    text = Path(config_path).read_text() if isinstance(config_path, (str, Path)) else None
    if text is None:
        return None
    config = {}
    for line in text.splitlines():
        m = re.match(r"^- (\w+):\s*([\d.]+),\s*([\d.]+),\s*(\w+),\s*([\d.]+)", line)
        if m:
            config[m.group(1)] = {
                "min": float(m.group(2)), "max": float(m.group(3)),
                "type": m.group(4), "weight": float(m.group(5)),
            }
    return config if config else None


def normalize_score(value, good_min, good_max, metric_type="higher_better"):
    """Normalize a metric value to 0-1 based on good range."""
    if value is None:
        return None
    if metric_type == "target_range":
        mid = (good_min + good_max) / 2
        half_range = (good_max - good_min) / 2
        if half_range < 1e-6:
            return 1.0 if abs(value - mid) < 1e-6 else 0.0
        deviation = abs(value - mid) / half_range
        return max(0.0, min(1.0, 1.0 - (deviation - 1.0))) if deviation > 1.0 else 1.0
    if metric_type == "lower_better":
        if value <= good_min:
            return 1.0
        if value >= good_max:
            return 0.0
        return 1.0 - (value - good_min) / (good_max - good_min)
    # higher_better (default)
    if value >= good_max:
        return 1.0
    if value <= good_min:
        return 0.0
    return (value - good_min) / (good_max - good_min)


def analyze_trajectory(end_effector_positions, grasp_states, contact_forces, dt, config_path=None):
    """Main entry point — called by evaluate_policy.py per scenario.

    Stub — Metric Design Agent fills in project-specific computation.

    Args:
        end_effector_positions: np.array (timesteps, 3) — xyz of end effector
        grasp_states: np.array (timesteps,) — binary 0/1 grasp active
        contact_forces: np.array (timesteps,) — grasp force magnitude, or None
        dt: float — simulation timestep
        config_path: optional path to monitor_config.md

    Returns:
        dict with raw metrics and normalized scores
    """
    tier2 = parse_tier2_config(config_path)

    # Stub metrics — replace with actual computation
    trajectory_jerk = None
    grasp_force_profile = None
    approach_directness = None

    sub_scores = {
        "trajectory_jerk_score": None,
        "grasp_force_profile_score": None,
        "approach_directness_score": None,
    }

    detailed_quality_score = None

    return {
        "trajectory_jerk": trajectory_jerk,
        "grasp_force_profile": grasp_force_profile,
        "approach_directness": approach_directness,
        "sub_scores": sub_scores,
        "detailed_quality_score": detailed_quality_score,
    }


def format_markdown(results, scenario_name):
    """Format eval quality metrics as markdown."""
    lines = [f"\n### Manipulation Quality — {scenario_name}"]
    for key in ("trajectory_jerk", "grasp_force_profile", "approach_directness"):
        val = results.get(key)
        lines.append(f"- **{key}**: {val:.4f}" if val is not None else f"- **{key}**: N/A")
    dqs = results.get("detailed_quality_score")
    lines.append(f"- **detailed_quality_score**: {dqs:.3f}" if dqs is not None else "- **detailed_quality_score**: N/A")
    return "\n".join(lines)
