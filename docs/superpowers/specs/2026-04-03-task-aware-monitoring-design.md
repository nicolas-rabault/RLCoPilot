# Task-Aware Monitoring with Quality Metrics & Human Feedback

**Date**: 2026-04-03
**Status**: Draft
**Problem**: The Monitor agent makes KEEP/BAD/FINISH decisions based on scalar WandB metrics, but these metrics have blind spots — particularly around behavior quality. A robot can have improving reward while exhibiting unnatural gait (jerky, asymmetric, arrhythmic). The current system cannot detect this autonomously, and when the user catches it visually, that feedback has no structured path back into the system.
**Solution**: Task-specific monitoring with two-tier quality metrics, a non-blocking human feedback loop, and a Metric Design Agent that tailors monitoring to each task.

---

## 1. Task-Specific Monitoring Architecture

### Current State

Monitoring is one-size-fits-all: a single `monitor.py` and `evaluate_policy.py` per project, with metrics hardcoded in `config.md`. All tasks share the same decision criteria and metric categories.

### New Structure

Each task gets its own monitoring directory with task-specific configs and scripts:

```
.claude/rl-training/
├── config.md                              # project-level config (gains Task monitoring field)
├── tasks/
│   └── <task-name>/                       # e.g., biped-locomotion
│       ├── monitor_config.md              # task-specific metrics, thresholds, quality definition
│       ├── monitor_metrics.py             # computes derived metrics from raw WandB data
│       └── eval_metrics.py               # computes detailed quality metrics during eval rollouts
├── scripts/
│   ├── monitor.py                         # generic WandB fetcher (unchanged)
│   ├── evaluate_policy.py                 # generic eval runner (calls task's eval_metrics.py)
│   └── ...
```

### Linkage

`config.md` gains a new field:

```markdown
## Monitoring
- Task monitoring: biped-locomotion
```

This points the Monitor cron to `.claude/rl-training/tasks/biped-locomotion/` for task-specific logic.

### Template Side (rlpilot)

```
templates/
├── tasks/
│   ├── locomotion/                        # starter templates for locomotion tasks
│   │   ├── monitor_config.md
│   │   ├── monitor_metrics.py
│   │   └── eval_metrics.py
│   ├── manipulation/                      # starter templates for manipulation tasks
│   │   └── ...
│   └── balance/                           # starter templates for balance tasks
│       └── ...
```

The Metric Design Agent uses these as starting points, then customizes for the specific robot and task.

---

## 2. Two-Tier Quality Metrics

### Tier 1 — Training-Time Metrics (Coarse, Every Monitor Tick)

Computed by `tasks/<name>/monitor_metrics.py` from raw WandB data already logged during training. Requires no training code changes.

**Interface:**

```
uv run .claude/rl-training/tasks/<name>/monitor_metrics.py <raw_metrics.json> [--previous <prev_derived.json>]
```

Input: JSON of raw WandB metrics (extracted from `<!-- RAW_METRICS:... -->` in monitor output).
Output: JSON of derived metrics + markdown summary appended to monitor file.

**For biped locomotion, derived metrics include:**

| Metric | Source | What it Detects |
|--------|--------|-----------------|
| `symmetry_ratio` (0-1) | Left vs right joint torques from `Torque/` | Asymmetric gait |
| `action_smoothness` | `Episode_Reward/action_rate_l2` promoted to monitored signal | Jerky motions |
| `survival_ratio` | `Episode_Termination/time_out` vs total terminations | Falling vs completing episodes |
| `reward_balance` | Ratio of locomotion rewards to regularization rewards | "Playing it safe" vs reward hacking |
| `quality_score` (0-1) | Weighted composite of above | Overall gait health |

The `monitor_config.md` defines weights for the composite and which sub-metrics to track.

### Tier 2 — Eval-Time Metrics (Detailed, When Eval Runs)

Computed by `tasks/<name>/eval_metrics.py` during policy evaluation with access to full simulation state (joint positions, contact forces, etc.).

**Interface:**

```python
# Called by evaluate_policy.py after each scenario rollout
# Receives trajectory data, returns detailed quality analysis
def analyze_trajectory(joint_positions, joint_velocities, contact_states, contact_forces, dt):
    return {
        "joint_jerk": ...,           # Mean jerk across joints (lower = smoother)
        "step_periodicity": ...,      # Dominant frequency strength from FFT on contacts (higher = more rhythmic)
        "stance_swing_ratio": ...,    # Per-foot, natural walking ~60/40
        "phase_offset": ...,          # L/R contact timing offset, walking ~0.5
        "grf_profile_score": ...,     # How close vertical force matches natural double-hump
        "detailed_quality_score": ..., # Composite (0-1)
    }
```

The eval script calls this per-scenario and includes results in `eval_metrics.md` and `eval_metrics.json`.

### How Tiers Interact

- Tier 1 runs every monitor tick (~33 min) — cheap, catches gross issues fast
- Tier 2 runs only during eval — expensive, provides deep diagnosis
- Both feed into the Monitor's decision logic
- Tier 1 quality_score dropping below `quality_score_bad_threshold` (from monitor_config.md) triggers an eval on the next monitor tick even if eval isn't normally scheduled, to get Tier 2 confirmation before making a KEEP/BAD decision

---

## 3. Non-Blocking Human Feedback Loop

### Principle

The ITERATE phase never waits for human input. Feedback is always optional, always async, but when present, it's structured and persistent.

### Flow

1. **Monitor kills a run** → writes `result.md` with a pre-filled Human Assessment section:
   ```markdown
   ## Human Assessment
   Tags: []
   Notes: No feedback yet.
   ```

2. **ITERATE starts immediately** — reads `result.md`, diagnoses, implements fix, relaunches. Does not wait.

3. **User provides feedback at any point** — in conversation naturally (e.g., "the gait looked asymmetric") or proactively. The agent:
   - Parses feedback into structured tags from a known vocabulary (e.g., `asymmetric_gait`, `jerky_motion`, `shuffling`, `reward_hacking`, `too_conservative`, `unstable_at_speed`)
   - Updates `result.md` in-place
   - Updates `session_state.json` iteration entry

4. **Session state tracks feedback history:**
   ```json
   "iterations": [
     {
       "run": 1,
       "result": "killed at step 36k, track_lin_vel halved",
       "human_feedback": {
         "tags": ["asymmetric_gait", "jerky_upper_body"],
         "notes": "Left leg swings wider than right, torso wobbles at higher speeds."
       }
     },
     {
       "run": 2,
       "result": "killed at step 24k, ang_vel collapsed",
       "human_feedback": null
     }
   ]
   ```

5. **Subsequent ITERATE phases read this history.** If runs 1-3 all got tagged `asymmetric_gait`, the diagnosis agent knows symmetry is a persistent problem and prioritizes it.

### Tag Vocabulary

Task-specific, defined in `monitor_config.md`. For biped locomotion:

```markdown
## Human Feedback Tags
- asymmetric_gait: Left/right legs behave differently
- jerky_motion: Abrupt, non-smooth movements
- shuffling: Feet barely leave the ground
- stumbling: Frequent near-falls or recovery motions
- reward_hacking: Achieves reward through unintended behavior
- too_conservative: Overly cautious, barely moving
- unstable_at_speed: Falls or wobbles at higher commanded velocities
- unnatural_posture: Body orientation or lean looks wrong
```

The agent can also accept free-text notes that don't map to tags.

---

## 4. Metric Design Agent

A dedicated agent that brainstorms task-specific monitoring metrics with the user, then generates the task monitoring directory.

### When It Runs

- **During SETUP** (Step 4: Monitoring & Evaluation): after robot/task info is gathered, before generating scripts. Replaces the current manual metric configuration for task-specific quality metrics.
- **On demand**: user says "improve monitoring for this task," or the ITERATE phase detects repeated failures that metrics didn't catch (e.g., 3+ iterations with human feedback tags that don't correspond to any monitored metric).

### What It Does

1. **Reads context**: robot type, actuators, task objective, simulator, existing reward terms, observation space, what's already logged to WandB

2. **Proposes metric categories** based on task type:
   - Locomotion → gait quality (symmetry, periodicity, smoothness, contact patterns)
   - Manipulation → grasp stability, approach trajectory, contact forces
   - Balance → CoM tracking, recovery time, base stability
   - Custom → asks user what "good" and "bad" look like

3. **Brainstorms with the user** (one question at a time):
   - "For a biped with dot contacts, symmetry and periodicity are critical. What does a bad gait look like for Leggy specifically?"
   - "Your reward already has `foot_slip` and `action_rate_l2` — should we promote those to monitored metrics?"
   - "What's the minimum gait quality you'd accept for a 'KEEP' decision?"

4. **Maps metrics to tiers**:
   - Scans training code for existing WandB logs
   - Tier 1 (derived from existing logs): no code changes needed
   - Tier 2 (eval-time): needs `eval_metrics.py` implementation
   - Tier 3 (needs new training logging): flags what would need to be added to the env — this becomes a task for the CODE phase if the user approves

5. **Generates the task directory:**
   - `monitor_config.md` — metrics, thresholds, weights, decision rules, feedback tags
   - `monitor_metrics.py` — Tier 1 derived metric computation
   - `eval_metrics.py` — Tier 2 detailed quality analysis

6. **Updates `config.md`** with the `Task monitoring: <task-name>` link

### Re-Invocation

After a session with repeated failures, the ITERATE phase can suggest: "Gait score didn't catch the asymmetry issue across runs 1-3. Want to refine the monitoring metrics?" This re-runs the Metric Design Agent with additional context:
- What was missed (human feedback tags with no corresponding metric)
- Which metrics were noisy or unhelpful (always near threshold, never triggered decisions)
- The full iteration history for this session

---

## 5. Monitor Cron Changes

### Updated Flow

```
STEP 0: Read context (unchanged)
  + Read tasks/<name>/monitor_config.md for task-specific thresholds

STEP 1: Phase check (unchanged)

STEP 2: Fetch metrics (unchanged output, new post-processing)
  + Extract raw metrics JSON from monitor output
  + Run: uv run .claude/rl-training/tasks/<name>/monitor_metrics.py <raw_metrics.json> [--previous <prev>]
  + Append derived metrics (quality score, sub-scores) to monitor_MMM.md

STEP 3: Evaluate policy (unchanged trigger, enriched output)
  + evaluate_policy.py calls tasks/<name>/eval_metrics.py on rollout data
  + Detailed quality breakdown added to eval_metrics.md and eval_metrics.json

STEP 4: Notification (enriched)
  + Include quality score and any flagged sub-scores in message
  + Example: "Monitor 5 — Run 2 (step 24k) | Reward: 85.3 ↑ | Gait: 0.71 ↓ (symmetry: 0.58 ⚠)"

STEP 5: DECIDE (expanded rules)
  Existing rules from config.md Decision Criteria still apply.
  New rules from monitor_config.md:
  - If reward improving but quality_score declining for 2+ monitors → BAD
  - If any quality sub-score below critical threshold (from monitor_config.md) → BAD
  - FINISH now also requires quality_score above minimum threshold
  Task-specific thresholds in monitor_config.md, not hardcoded.

STEP 6: ACT (enriched result.md)
  On KILL:
  - result.md includes quality metrics trend across all monitors
  - result.md includes pre-filled Human Assessment section
  - result.md notes which quality sub-scores triggered the kill (if applicable)
```

### What Doesn't Change

- Cron lifecycle (create after LAUNCH, delete on KILL/FINISH/stale)
- Session state management and `consecutive_bad` counter
- Self-deletion logic
- Overall KEEP/BAD/FINISH framework — quality metrics are additional signals, not a replacement

---

## 6. Config Changes

### config.md Template Additions

```markdown
## Monitoring
- Tool: wandb
- Task monitoring: <task-name>              # NEW — points to tasks/<task-name>/
- Metric categories: [...]
- Key metrics: [...]
- Kill threshold: 2
- Max iterations: 10
```

### monitor_config.md (New File, Per Task)

```markdown
# Monitoring Configuration — <task-name>

## Task Type
<locomotion | manipulation | balance | custom>

## Tier 1 Metrics (Derived from WandB)
| Metric | Source | Weight in Quality Score |
|--------|--------|------------------------|
| symmetry_ratio | Torque/* L/R comparison | 0.3 |
| action_smoothness | Episode_Reward/action_rate_l2 | 0.2 |
| survival_ratio | Episode_Termination/* | 0.2 |
| reward_balance | Episode_Reward/* ratios | 0.3 |

## Tier 2 Metrics (Eval-Time)
| Metric | Description |
|--------|-------------|
| joint_jerk | Mean jerk across joints |
| step_periodicity | FFT dominant frequency strength |
| stance_swing_ratio | Per-foot ground/air time |
| phase_offset | L/R contact timing offset |
| grf_profile_score | Vertical force pattern naturalness |

## Decision Rules
- quality_score_bad_threshold: 0.4
- quality_declining_monitors: 2
- quality_finish_minimum: 0.7
- reward_vs_quality_divergence: true

## Human Feedback Tags
- asymmetric_gait: Left/right legs behave differently
- jerky_motion: Abrupt, non-smooth movements
- shuffling: Feet barely leave the ground
- stumbling: Frequent near-falls or recovery motions
- reward_hacking: Achieves reward through unintended behavior
- too_conservative: Overly cautious, barely moving
- unstable_at_speed: Falls or wobbles at higher commanded velocities
- unnatural_posture: Body orientation or lean looks wrong
```

---

## 7. SKILL.md Changes

### SETUP Phase

Step 4 (Monitoring & Evaluation) is split:

- **Step 4a**: Generic monitoring setup (WandB access, notification config) — unchanged
- **Step 4b**: Spawn **Metric Design Agent** to brainstorm and generate task-specific monitoring. This is interactive — the agent asks questions one at a time to understand what "good" and "bad" look like for this task, proposes metrics, and generates the task directory.
- **Step 4c**: Monitoring validation on hosts — unchanged

### MONITOR Cron Prompt

Updated to include:
- Reading `tasks/<name>/monitor_config.md`
- Running `tasks/<name>/monitor_metrics.py` after fetching WandB metrics
- Passing task config to `evaluate_policy.py` for Tier 2 metrics
- Using task-specific decision rules alongside existing ones
- Including quality scores in notifications
- Writing enriched `result.md` with Human Assessment section on kill

### ITERATE Phase

Step 1 (DIAGNOSE) updated to:
- Read `human_feedback` from previous iterations in `session_state.json`
- Read quality sub-scores from monitor files to identify which aspect degraded
- If 3+ iterations share the same human feedback tag with no corresponding metric improvement, suggest re-running the Metric Design Agent

Step between DIAGNOSE and IMPLEMENT:
- In the same message as the diagnosis summary, include: "How did the gait look in the last run? If you have feedback, I'll incorporate it — otherwise I'm proceeding with the metrics-based diagnosis."
- This is a single message, not a blocking wait. The agent continues to IMPLEMENT in the same turn.
- If the user later provides feedback (in a follow-up message, or during any subsequent interaction), the agent parses it into tags and updates `result.md` and `session_state.json` for the relevant iteration. This feedback is then available to future ITERATE phases.

---

## 8. Summary of All Changes

| Component | Change |
|-----------|--------|
| `templates/config.md` | Add `Task monitoring` field |
| `templates/tasks/` | New directory with locomotion/manipulation/balance starter templates |
| `templates/scripts/monitor.py` | Unchanged (raw fetcher) |
| `templates/scripts/evaluate_policy.py` | Call task's `eval_metrics.py` after rollouts |
| `skills/rlpilot/SKILL.md` | SETUP gains Metric Design Agent step; MONITOR cron prompt expanded; ITERATE gains human feedback handling |
| Per-project `.claude/rl-training/tasks/<name>/` | New directory generated by Metric Design Agent |
| Per-project `session_state.json` | `human_feedback` field added to iterations |
| Per-project `result.md` | Human Assessment section added |
