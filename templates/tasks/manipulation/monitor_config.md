# Monitoring Configuration — <task-name>

## Task Type
manipulation

## Quality Metrics — Tier 1 (Derived from WandB)

| Metric | Source | Weight | Description |
|--------|--------|--------|-------------|
| grasp_stability | Grasp reward terms | 0.3 | Consistency of grasp across episodes |
| approach_smoothness | Action rate metrics | 0.2 | Smoothness of approach trajectory |
| success_rate | Episode success/failure | 0.3 | Fraction of successful task completions |
| force_efficiency | Contact force metrics | 0.2 | Appropriate force usage (not too high/low) |

## Quality Metrics — Tier 2 (Eval-Time)

| Metric | Description | Good Range |
|--------|-------------|------------|
| trajectory_jerk | End-effector trajectory smoothness | < 20.0 |
| grasp_force_profile | Force application pattern during grasp | > 0.5 |
| approach_directness | Path efficiency (straight line ratio) | > 0.7 |

## Decision Rules

- quality_score_bad_threshold: 0.4
- quality_declining_monitors: 2
- quality_finish_minimum: 0.7
- reward_vs_quality_divergence: true

## Human Feedback Tags

- fumbling: Unstable or uncertain grasping
- excessive_force: Applying too much contact force
- inefficient_path: Taking unnecessary detours to reach target
- dropping: Failing to maintain grasp during transport
- collision: Hitting obstacles or unintended surfaces
- too_slow: Overly cautious movements

## Tag-to-Metric Mapping

- fumbling → grasp_stability
- excessive_force → force_efficiency
- inefficient_path → approach_smoothness
- dropping → grasp_stability
- collision → (no metric)
- too_slow → (no metric)

## Tier 2 Normalization

- trajectory_jerk: 0, 50, lower_better, 0.35
- grasp_force_profile: 0, 1, higher_better, 0.35
- approach_directness: 0, 1, higher_better, 0.30
