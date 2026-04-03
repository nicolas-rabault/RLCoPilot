#!/usr/bin/env python3
"""Compute task-specific derived quality metrics for manipulation tasks.

Usage:
    uv run .claude/rl-training/tasks/<name>/monitor_metrics.py <raw_metrics.json> [--previous <prev.json>] [--config <monitor_config.md>]

Stub template — the Metric Design Agent customizes metric computation per project.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_monitor_config(config_path):
    """Extract weights and thresholds from monitor_config.md."""
    text = Path(config_path).read_text()
    weights = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*(\w+)\s*\|.*\|\s*([\d.]+)\s*\|", line)
        if m and m.group(1) not in ("Metric",):
            weights[m.group(1)] = float(m.group(2))
    return {"weights": weights}


def compute_quality_score(sub_scores, weights):
    """Weighted composite with coverage tracking."""
    total_weight = 0.0
    weighted_sum = 0.0
    missing = []
    for name in weights:
        score = sub_scores.get(name)
        if score is not None:
            weighted_sum += score * weights[name]
            total_weight += weights[name]
        else:
            missing.append(name)
    expected_weight = sum(weights.values())
    coverage = total_weight / expected_weight if expected_weight > 1e-6 else 0.0
    quality = max(0.0, min(1.0, weighted_sum / total_weight)) if total_weight > 1e-6 else None
    return quality, coverage, missing


def format_markdown(derived, previous):
    """Format derived metrics as markdown summary."""
    lines = ["\n## Quality Metrics (Tier 1)"]
    for name, val in derived.items():
        if name in ("coverage", "missing"):
            continue
        if val is None:
            lines.append(f"- **{name}**: N/A")
            continue
        if not isinstance(val, (int, float)):
            continue
        trend = ""
        if previous and name in previous and isinstance(previous.get(name), (int, float)):
            diff = val - previous[name]
            if abs(diff) > 0.01:
                trend = f" ({'↑' if diff > 0 else '↓'} {abs(diff):.2f})"
            else:
                trend = " (stable)"
        lines.append(f"- **{name}**: {val:.3f}{trend}")
    cov = derived.get("coverage", 1.0)
    missing = derived.get("missing", [])
    if cov < 1.0:
        lines.append(f"- **coverage**: {cov:.0%} — missing: {', '.join(missing)}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_metrics", help="Path to raw metrics JSON file")
    parser.add_argument("--previous", help="Path to previous derived metrics JSON")
    parser.add_argument("--config", default=".claude/rl-training/tasks/manipulation/monitor_config.md")
    args = parser.parse_args()

    metrics = json.loads(Path(args.raw_metrics).read_text())
    config = parse_monitor_config(args.config)

    previous = None
    if args.previous:
        p = Path(args.previous)
        if p.exists():
            previous = json.loads(p.read_text())

    # Stub sub-scores — Metric Design Agent replaces these with project-specific logic
    sub_scores = {
        "grasp_stability": None,
        "approach_smoothness": None,
        "success_rate": None,
        "force_efficiency": None,
    }

    quality, coverage, missing = compute_quality_score(sub_scores, config["weights"])
    derived = {**sub_scores, "quality_score": quality, "coverage": coverage, "missing": missing}

    print(json.dumps(derived))
    print(format_markdown(derived, previous), file=sys.stderr)


if __name__ == "__main__":
    main()
