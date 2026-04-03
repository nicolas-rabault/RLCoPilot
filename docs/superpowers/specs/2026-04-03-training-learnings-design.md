# Training Learnings — Design Spec

**Date:** 2026-04-03
**Status:** Draft

## Problem

Training sessions generate valuable insights — what works, what fails, physical limits, reward pitfalls — but this knowledge lives scattered across `result.md`, `analysis.md`, metrics files, and human feedback. Each new session starts from scratch without benefiting from previous experiments.

## Solution

A shared living document (`docs/training-learnings.md`) that accumulates actionable, proven training tips across all tasks and sessions. A background learning agent analyzes each run's data and updates the document. CODE and ITERATE phases read it to avoid repeating mistakes and build on what works.

## Architecture

Two components:

1. **`learnings.py`** — Deterministic script that gathers and structures run data into a report
2. **Learning agent** — LLM subagent that reads the report + current learnings doc and decides what to update

This follows the existing project pattern: deterministic scripts for data, LLM for judgment.

## The Learnings Document

**Location:** `docs/training-learnings.md`

**Structure:** Categorized by topic, shared across all tasks.

```markdown
# Training Learnings

Actionable tips and insights accumulated from training experiments.
Each entry is backed by observed evidence from training runs.

## Reward Design
- <tip>

## Observation Space
- <tip>

## Training Hyperparameters
- <tip>

## Physical Limits & Robot Capabilities
- <tip>

## Common Failure Modes
- <tip>

## What Doesn't Work
- <tip>
```

**Properties:**
- Each entry is a concise, actionable bullet
- Entries can be task-qualified inline (e.g., "For locomotion: ...")
- The agent can add/remove/update categories as the document evolves — these are the starting set
- Entries get updated or removed when new evidence contradicts them — living doc, not append-only log

## The Script — `learnings.py`

**Location:** `.claude/rl-training/scripts/learnings.py`
**Template:** `templates/scripts/learnings.py`

**Interface:**
```bash
uv run learnings.py <session_dir> --run N
```

**Inputs:**
- `run_NNN/result.md` — what happened, why training was killed/finished/paused
- `run_NNN/analysis.md` — diagnosis and hypothesis
- `run_NNN/derived_metrics_*.json` — quality metric progression
- `run_NNN/raw_metrics_*.json` — reward curves, step counts
- `session_state.json` — goal, iteration history, human feedback across all runs
- Git diff of code changes for this iteration (via `git log --patch` on the branch)

**Output:** Structured markdown report to stdout:

```markdown
## Run Summary
- Goal: <from session_state>
- Task: <from config>
- Run: N of M total iterations
- Outcome: KILLED / FINISHED / PAUSED
- Reason: <from result.md>

## Metrics Trajectory
- Starting quality_score: X → Final: Y
- Key sub-scores: symmetry: A→B, smoothness: C→D, ...
- Reward trend: <improving/plateauing/degrading>

## Diagnosis & Fix
- Hypothesis: <from analysis.md>
- Code changes: <summary of diff>
- Did the fix help? <yes/no/inconclusive based on metrics>

## Human Feedback
- Tags: [list]
- Notes: <verbatim>

## Iteration History Context
- Previous iterations that shared similar diagnosis or feedback tags
- Pattern: <if any recurring theme across iterations>
```

**Properties:**
- Task-agnostic — one template, not per-task variants
- Handles missing files gracefully (no `analysis.md` on FINISH, no human feedback on early runs, variable monitor snapshot counts)
- Does no judgment — structures data only

## The Learning Agent

### When it runs

| Trigger | Mode | Reason |
|---------|------|--------|
| ITERATE phase, after CODE REVIEW, before RELAUNCH | **Background** | Don't delay relaunch |
| FINISH decision (monitor cron) | **Foreground** | No relaunch coming, capture success insights |
| PAUSED decision (monitor cron) | **Foreground** | No relaunch coming, capture failure patterns |

### Agent prompt context

1. Output of `uv run learnings.py <session_dir> --run N`
2. Current contents of `docs/training-learnings.md`
3. Instructions:
   - Update the learnings doc with new insights
   - Remove or update outdated entries if contradicted by new evidence
   - Keep entries concise and actionable
   - Use existing categories or create new ones if needed
   - Use agent judgment to assess significance — write directly, no staging

### Agent behavior

1. Read the structured report from `learnings.py`
2. Read `docs/training-learnings.md`
3. Decide if anything is worth adding, updating, or removing
4. Edit the file (or do nothing if no new insight)
5. Commit the change with a descriptive message (e.g., `learnings: reward shaping below 0.01 causes instability`)

## Integration with Existing Phases

### CODE phase — step 1 (INVESTIGATE)

Add `docs/training-learnings.md` to the list of files the agent reads before brainstorming changes. This gives the coding agent awareness of known pitfalls and proven techniques.

### ITERATE phase — step 1 (DIAGNOSE)

Add `docs/training-learnings.md` to the diagnosis context. The agent checks if the current failure matches a known pattern from past learnings, avoiding repeated mistakes.

### ITERATE phase — after step 5 (CODE REVIEW)

Spawn the learning agent as a **background** subagent before proceeding to RELAUNCH (step 6). The agent runs concurrently with the next training launch.

### MONITOR CRON — FINISH decision (step 6)

Spawn the learning agent as a **foreground** step before invoking `superpowers:finishing-a-development-branch`.

### MONITOR CRON — PAUSED decision (step 6)

Spawn the learning agent as a **foreground** step before setting phase to PAUSED and notifying the user.

## Changes Summary

| What | Where | Change |
|------|-------|--------|
| New template | `templates/scripts/learnings.py` | Data extraction script |
| New doc | `docs/training-learnings.md` | Empty template created during SETUP; populated by learning agent |
| SKILL.md — SETUP | Phase 0, step 8 | Generate `learnings.py` from template |
| SKILL.md — CODE | Phase 2, step 1 (INVESTIGATE) | Read `docs/training-learnings.md` |
| SKILL.md — ITERATE | Phase 4, after CODE REVIEW | Spawn learning agent (background) |
| SKILL.md — ITERATE | Phase 4, step 1 (DIAGNOSE) | Read `docs/training-learnings.md` |
| SKILL.md — MONITOR CRON | FINISH decision | Spawn learning agent (foreground) |
| SKILL.md — MONITOR CRON | PAUSED decision | Spawn learning agent (foreground) |

**Purely additive** — no changes to existing scripts, decision logic, metrics, or feedback loop.
