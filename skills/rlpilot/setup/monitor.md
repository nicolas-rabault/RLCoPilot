# SETUP-MONITOR

You are configuring monitoring and evaluation for RL training. This phase runs two sequential sub-agents.

## Context

The following config has already been gathered:

<CONFIG_CONTEXT>
{orchestrator injects Robot, Task, Source Files sections from config.md here}
</CONFIG_CONTEXT>

## Sub-agent 1: Metric Design

### Purpose
Design WandB monitoring metrics, thresholds, and decision rules.

### Process (interactive)

Ask the user (one question at a time):
- What monitoring tool? (WandB, TensorBoard, local logs)
- If WandB: project path (e.g. `team/project`) → store in project memory file `rl_training_infra.md`
- Key metric categories and prefixes to track

If `## Monitoring` section already exists in config.md, skip these questions — the user already answered them. Go straight to the Metric Design Agent.

### Metric Design Agent (interactive)

Spawn the Metric Design Agent to brainstorm and generate task-specific monitoring. This agent:

1. Reads context: robot type, actuators, task objective, simulator, existing reward terms, observation space. Scans the training code for existing WandB log calls to identify what's already logged.

2. Proposes metric categories based on task type:
   - Locomotion → gait quality (symmetry, periodicity, smoothness, contact patterns)
   - Manipulation → grasp stability, approach trajectory, contact forces
   - Balance → CoM tracking, recovery time, base stability
   - Custom → asks user what "good" and "bad" look like

3. Brainstorms with the user (one question at a time):
   - What does a bad behavior look like for this specific robot?
   - Which existing reward terms should be promoted to monitored quality metrics?
   - What's the minimum quality you'd accept for a KEEP decision?

4. Maps metrics to tiers:
   - Tier 1 (derived from existing WandB logs): no training code changes needed
   - Tier 2 (eval-time from simulation state): needs eval_metrics.py
   - Tier 3 (needs new training-time logging): flags for CODE phase if user approves

5. Generates the task monitoring directory using templates from `${CLAUDE_PLUGIN_ROOT}/templates/tasks/<task-type>/` as starting points:
   - `.claude/rl-training/tasks/<task-name>/monitor_config.md` — metrics, thresholds, weights, decision rules, human feedback tags
   - `.claude/rl-training/tasks/<task-name>/monitor_metrics.py` — Tier 1 derived metric computation

### Metric Design Output

Append to `.claude/rl-training/config.md`:

```markdown
## Monitoring
- Tool: <wandb, tensorboard, local>
- Task monitoring: <task-name>
- Metric categories: [<prefix1/>, <prefix2/>, ...]
- Key metrics: [<metric1>, <metric2>, ...]
- Kill threshold: 2
- Max iterations: 10

## Decision Criteria
- KEEP: <when to keep training>
- BAD: <when training is going wrong>
- FINISH: <when training is done>
```

If WandB is chosen, write `rl_training_infra.md` to project memory with WandB project path and entity.

### Metric Design Checkpoint

Sub-agent 1 is done when `monitor_config.md` exists in `.claude/rl-training/tasks/<task-name>/`.

---

## Sub-agent 2: Eval Design

### Purpose
Design the evaluation script through brainstorming — the most important part of the training skill. This agent deeply understands the task and creates a custom evaluation pipeline with behavioral prints that give the monitoring agent maximum information for decision-making.

### Process

1. **Template learning**: Before brainstorming, scan existing `.claude/rl-training/tasks/*/` directories for `evaluate_policy.py` and `eval_metrics.py` files. Read them to understand patterns and approaches used for other tasks. Summarize what you found to inform the brainstorm.

2. **Invoke `superpowers:brainstorming`**: Design the evaluation strategy for this specific task. Feed the brainstorming with:
   - Robot context from config.md (type, actuators, specificities)
   - Task objective and scenarios from config.md
   - Monitoring metrics from `monitor_config.md` (designed by sub-agent 1)
   - Patterns learned from existing eval scripts (step 1)
   - The constraint that eval runs every ~30 min monitoring tick, so it must complete in a few minutes

   The brainstorming should explore:
   - What behavioral information best serves the monitoring agent's decisions?
   - What does "good" vs "bad" look like in practice for this robot/task?
   - What prints would make the difference between a useful eval and a useless one?
   - What level of interpretation should the script do (raw data, detected events, layered)?
   - How to structure the output for both quick decisions and deep investigation?

3. **Generate eval files** based on the brainstorming design:
   - `.claude/rl-training/tasks/<task-name>/evaluate_policy.py` — task-specific evaluation script with custom behavioral prints
   - `.claude/rl-training/tasks/<task-name>/eval_metrics.py` — Tier 2 detailed quality analysis
   - Make both executable: `chmod +x`

   The eval script must produce these output files:
   - `eval_report.md` — behavioral report (the monitoring agent's primary eval input)
   - `eval_metrics.json` — machine-readable metrics for `decide.py`
   - `eval_raw_data.json` — per-timestep raw data for deep investigation
   - `*.mp4` — video for Discord notification (not for evaluation)

   The eval report must follow this structure:
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
   <patterns across scenarios>

   ## Raw Metrics
   <!-- RAW_METRICS:{json}-->
   ```

4. **Dry-run validation**: Run the eval script locally with a random policy to verify the pipeline works end-to-end.
   ```bash
   uv run .claude/rl-training/tasks/<task-name>/evaluate_policy.py --dry-run --output-dir /tmp/eval-dry-run/ --config .claude/rl-training/config.md
   ```
   The `--dry-run` flag makes the script:
   - Instantiate the environment
   - Use a random policy (no checkpoint needed)
   - Run a small number of steps per scenario (e.g. 10 instead of the full count)
   - Produce all output files (eval_report.md, eval_metrics.json, eval_raw_data.json, video)

   Verify:
   - Exit code is 0
   - `eval_report.md` exists and contains all expected sections
   - `eval_metrics.json` is valid JSON
   - `eval_raw_data.json` is valid JSON
   - Behavioral prints are present and meaningful (not empty placeholders)

   If the dry-run fails, read the error, fix the script, and retry. Repeat until the dry-run passes.

5. **Write validation marker**: After dry-run passes, create `.claude/rl-training/tasks/<task-name>/.eval_validated` with the current timestamp.

### Eval Design Output

Append to `.claude/rl-training/config.md`:

```markdown
## Evaluation
- Scenarios:
  - <name>: <params>
- Video: true
```

### Eval Design Checkpoint

Sub-agent 2 is done when `.claude/rl-training/tasks/<task-name>/.eval_validated` exists.
