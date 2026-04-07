# Evaluation Redesign — Spec

## Problem

The current evaluation system has three weaknesses:

1. **SETUP-GENERATE silently skips eval validation** — the eval script is generated but never tested during setup. The agent assumes it can't run locally (it can — MuJoCo works on Mac without GPU).
2. **Video is for notifications, not evaluation** — the video is attached to Discord but nobody analyzes it. The real evaluation signal should come from extensive behavioral prints that an LLM agent can read and reason about.
3. **No dedicated evaluation design** — eval is an afterthought buried in the monitoring cron as an optional step. It should be the most important part of the skill, with its own brainstorming session and mandatory execution every monitoring tick.

## Design

### SETUP-MONITOR restructuring

SETUP-MONITOR becomes two sequential sub-agents:

**Sub-agent 1: Metric Design** (unchanged from today)
- Brainstorms WandB monitoring metrics, thresholds, decision rules
- Outputs: `monitor_config.md`, `monitor_metrics.py`
- Checkpoint: `monitor_config.md` exists

**Sub-agent 2: Eval Design** (new)
- Invokes `superpowers:brainstorming` to deeply understand the task and design evaluation
- Before brainstorming, scans existing `tasks/*/evaluate_policy.py` and `tasks/*/eval_metrics.py` for patterns to learn from (template learning)
- Brainstorms with the user: what behavioral information best serves the monitoring agent's decisions? What does "good" vs "bad" look like in practice for this robot/task? What prints would make the difference between a useful eval and a useless one?
- Generates: task-specific `evaluate_policy.py` (with custom behavioral prints) and `eval_metrics.py`
- **Dry-run validation**: instantiates the environment with a random policy, runs a few steps per scenario, verifies the script produces correct output (metrics files, behavioral prints, video). Runs locally — no GPU required for MuJoCo
- Checkpoint: `evaluate_policy.py` exists AND dry-run passed (`.eval_validated` marker file)
- If dry-run fails, the agent fixes the script and retries

### Eval script output structure

The eval script produces a behavioral report designed to give the monitoring agent maximum information. The brainstorming session determines the exact content, but the report has a fixed structure:

**Output files:**
- `eval_report.md` — the main behavioral report (what the monitoring agent reads)
- `eval_metrics.json` — machine-readable metrics for `decide.py`
- `eval_raw_data.json` — per-timestep raw data (joint positions, velocities, contacts, forces) for deep investigation
- `*.mp4` — video for Discord notification (not for evaluation)

**Report structure (template — brainstorming customizes the content):**
```markdown
# Behavioral Evaluation Report

## Summary
<high-level verdict: what the robot is doing well, what it's doing badly>

## Per-Scenario Results
### <scenario_name> (vx=X, vy=Y, vz=Z)
- Tracking performance: <velocity errors>
- Behavioral observations: <task-specific prints designed during brainstorm>
- Notable events: <stumbles, anomalies, phase transitions>
- Quality score: <composite>

## Cross-Scenario Analysis
<patterns across scenarios — e.g. "robot handles forward well but falls on turns">

## Raw Metrics
<!-- RAW_METRICS:{json}-->
```

The **Behavioral observations** and **Notable events** sections are what the brainstorming designs. They're task-specific — for a biped it might be gait symmetry and foot contact patterns, for a manipulator it might be grasp stability and approach trajectory. The brainstorming determines the best approach for what to print (raw data, interpreted events, or layered) based on what gives the monitoring agent the best information to make decisions.

### Eval as mandatory step with hard gate for FINISH

**Every monitoring tick runs eval.** It's no longer optional or conditional.

**Updated monitoring cron flow:**
```
fetch WandB metrics → compute quality → run eval → read behavioral report → decide → act
```

**Decision rules:**
- **KEEP/BAD decisions**: driven by WandB metrics (fast feedback), but the behavioral report is available as context for notifications and trend tracking
- **FINISH decision**: WandB metrics can suggest FINISH, but eval must confirm. If eval quality is below `quality_finish_minimum` threshold, decision downgrades to KEEP
- **Behavioral trend tracking**: since eval runs every tick, the monitoring agent can compare behavioral reports across ticks — detecting improvements or regressions in actual robot behavior

**Changes to `decide.py`:**
- New input: `--eval-report <path>` — incorporates eval quality into FINISH confirmation
- FINISH requires: `detailed_quality_score >= quality_finish_minimum` from eval

**Eval speed constraint:** since eval runs every ~30 min tick, the eval script needs to complete in a few minutes. The brainstorming session factors this into scenario and step count design.

### SETUP-GENERATE changes

SETUP-GENERATE no longer generates `evaluate_policy.py` — that's now created and validated by SETUP-MONITOR's Eval Design sub-agent.

**SETUP-GENERATE still generates:** `init_session.sh`, `get_latest_run.py`, `monitor.py`, `learnings.py`

**Checkpoint updates:**
- SETUP-MONITOR done signal: `monitor_config.md` exists AND `.eval_validated` marker exists
- SETUP-GENERATE done signal: `monitor.py` exists (no longer checks `evaluate_policy.py`)

The `templates/scripts/evaluate_policy.py` template becomes a reference example rather than a generation source.

## Files affected

| File | Change |
|------|--------|
| `skills/rlpilot/setup/monitor.md` | Add Eval Design sub-agent with brainstorming, template learning, dry-run validation |
| `skills/rlpilot/setup/generate.md` | Remove `evaluate_policy.py` from generation list |
| `skills/rlpilot/SKILL.md` | Update monitoring cron: eval mandatory every tick, eval as hard gate for FINISH, behavioral report as decision input |
| `templates/scripts/evaluate_policy.py` | Demote to reference example |

## Not changed

- KEEP/BAD still driven by WandB metrics for fast feedback
- Host setup, notifications, session management unchanged
- Tier 1 derived metrics unchanged
- Decision engine logic unchanged except adding eval hard gate for FINISH
- SETUP phase order unchanged: SETUP-DISCOVER → SETUP-MONITOR → SETUP-HOSTS → SETUP-NOTIFY → SETUP-GENERATE
