````markdown
# SETUP-GENERATE

You are generating the shared scripts for RL training. This is fully autonomous — no user interaction needed.

## Context

<CONFIG_CONTEXT>
{orchestrator injects complete config.md here}
</CONFIG_CONTEXT>

<HOST_CONFIGS>
{orchestrator injects all hosts/<name>/host.md contents here}
</HOST_CONFIGS>

<TASK_MONITOR_CONFIG>
{orchestrator injects tasks/<task-name>/monitor_config.md here}
</TASK_MONITOR_CONFIG>

<INFRA_MEMORY>
{orchestrator injects rl_training_infra.md here}
</INFRA_MEMORY>

## Generate Scripts

Generate shared scripts in `.claude/rl-training/scripts/`, using templates from `${CLAUDE_PLUGIN_ROOT}/templates/scripts/` as a starting point and adapting to the project:

1. `init_session.sh` — session state management (branch-based)
2. `get_latest_run.py` — find active run (WandB or other, based on Monitoring tool in config)
3. `monitor.py` — fetch metrics and format markdown report
4. `evaluate_policy.py` — headless eval with video and metrics (framework-specific, generated from scratch based on the project's RL framework from config)
5. `learnings.py` — gather structured run data for the learning agent

**Do NOT generate:** `notify.sh` (already created by SETUP-NOTIFY), per-host scripts (already created by SETUP-HOSTS), task monitoring files (already created by SETUP-MONITOR).

## Generate Training Learnings Template

Create `docs/training-learnings.md` if it doesn't exist:

```markdown
# Training Learnings

Actionable tips and insights accumulated from training experiments.
Each entry is backed by observed evidence from training runs.

## Reward Design

## Observation Space

## Training Hyperparameters

## Physical Limits & Robot Capabilities

## Common Failure Modes

## What Doesn't Work
```

## Finalize

- Make all scripts executable: `chmod +x .claude/rl-training/scripts/*.sh .claude/rl-training/scripts/*.py`
- Present a summary of all generated files to the user for review, listing each file and its purpose
````
