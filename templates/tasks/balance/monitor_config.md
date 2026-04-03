# Monitoring Configuration — <task-name>

## Task Type
balance

## Quality Metrics — Tier 1 (Derived from WandB)

| Metric | Source | Weight | Description |
|--------|--------|--------|-------------|
| com_stability | CoM tracking metrics | 0.3 | Center of mass deviation from target |
| recovery_speed | Episode length after perturbation | 0.2 | How quickly robot recovers from disturbances |
| posture_score | Upright/pose reward terms | 0.3 | Quality of maintained posture |
| energy_efficiency | Torque/action metrics | 0.2 | Energy usage for balance maintenance |

## Quality Metrics — Tier 2 (Eval-Time)

| Metric | Description | Good Range |
|--------|-------------|------------|
| com_jerk | CoM trajectory smoothness | < 10.0 |
| ankle_strategy_score | Use of ankle vs hip strategy | > 0.5 |
| base_oscillation | Frequency and amplitude of body sway | < 0.3 |

## Decision Rules

- quality_score_bad_threshold: 0.4
- quality_declining_monitors: 2
- quality_finish_minimum: 0.7
- reward_vs_quality_divergence: true

## Human Feedback Tags

- wobbling: Excessive oscillation during balance
- stiff: Overly rigid posture, not natural
- overcorrecting: Large corrective movements for small disturbances
- drifting: Slowly moving away from target position
- collapsing: Gradual loss of posture over time

## Tag-to-Metric Mapping

- wobbling → com_stability
- stiff → energy_efficiency
- overcorrecting → com_stability
- drifting → posture_score
- collapsing → posture_score

## Tier 2 Normalization

- com_jerk: 0, 20, lower_better, 0.35
- ankle_strategy_score: 0, 1, higher_better, 0.35
- base_oscillation: 0, 0.5, lower_better, 0.30
