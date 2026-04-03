#!/usr/bin/env python3
"""Compute detailed quality metrics for balance tasks during evaluation.

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
    if metric_type == "lower_better":
        if value <= good_min:
            return 1.0
        if value >= good_max:
            return 0.0
        return 1.0 - (value - good_min) / (good_max - good_min)
    if value >= good_max:
        return 1.0
    if value <= good_min:
        return 0.0
    return (value - good_min) / (good_max - good_min)


def analyze_trajectory(com_positions, joint_torques, base_orientation, dt, config_path=None):
    """Main entry point — called by evaluate_policy.py per scenario.

    Stub — Metric Design Agent fills in project-specific computation.

    Args:
        com_positions: np.array (timesteps, 3) — center of mass xyz
        joint_torques: np.array (timesteps, num_joints)
        base_orientation: np.array (timesteps, 4) — quaternion
        dt: float — simulation timestep
        config_path: optional path to monitor_config.md

    Returns:
        dict with raw metrics and normalized scores
    """
    tier2 = parse_tier2_config(config_path)

    # Stub metrics — replace with actual computation
    com_jerk = None
    ankle_strategy_score = None
    base_oscillation = None

    sub_scores = {
        "com_jerk_score": None,
        "ankle_strategy_score_score": None,
        "base_oscillation_score": None,
    }

    detailed_quality_score = None

    return {
        "com_jerk": com_jerk,
        "ankle_strategy_score": ankle_strategy_score,
        "base_oscillation": base_oscillation,
        "sub_scores": sub_scores,
        "detailed_quality_score": detailed_quality_score,
    }


def format_markdown(results, scenario_name):
    """Format eval quality metrics as markdown."""
    lines = [f"\n### Balance Quality — {scenario_name}"]
    for key in ("com_jerk", "ankle_strategy_score", "base_oscillation"):
        val = results.get(key)
        lines.append(f"- **{key}**: {val:.4f}" if val is not None else f"- **{key}**: N/A")
    dqs = results.get("detailed_quality_score")
    lines.append(f"- **detailed_quality_score**: {dqs:.3f}" if dqs is not None else "- **detailed_quality_score**: N/A")
    return "\n".join(lines)
