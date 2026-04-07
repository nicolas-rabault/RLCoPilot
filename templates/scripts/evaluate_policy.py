#!/usr/bin/env python3
"""REFERENCE EXAMPLE — not used for generation.

This file is a reference showing the general structure of an evaluation script.
The actual evaluate_policy.py for each task is created by SETUP-MONITOR's Eval Design
sub-agent through brainstorming, tailored to the specific task with custom behavioral prints.

See: skills/rlpilot/setup/monitor.md (Sub-agent 2: Eval Design)
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


def load_task_eval_metrics(config_path):
    """Load the task-specific eval_metrics module if configured."""
    text = Path(config_path).read_text()
    task_match = re.search(r"^- Task monitoring:\s*(.+)$", text, re.MULTILINE)
    if not task_match:
        return None
    task_name = task_match.group(1).strip()
    eval_path = Path(f".claude/rl-training/tasks/{task_name}/eval_metrics.py")
    if not eval_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("eval_metrics", eval_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_config(config_path):
    """Parse evaluation config from a markdown-style config file."""
    text = Path(config_path).read_text()
    config = {}

    num_steps_match = re.search(r"^- Eval steps:\s*(\d+)$", text, re.MULTILINE)
    if num_steps_match:
        config["num_steps"] = int(num_steps_match.group(1))
    else:
        config["num_steps"] = 500

    commands_match = re.search(r"^- Eval commands:\s*(.+)$", text, re.MULTILINE)
    if commands_match:
        config["commands"] = [c.strip() for c in commands_match.group(1).split(",")]
    else:
        config["commands"] = ["forward", "backward", "turn_left", "turn_right"]

    return config


def evaluate(checkpoint_path, config_path, output_path=None):
    """Run policy evaluation and write a markdown report."""
    config = parse_config(config_path)
    num_steps = config["num_steps"]
    commands = config["commands"]

    # NOTE: Framework-specific imports and env setup go here.
    # The SETUP phase replaces this block with project-specific code.
    # Example (Isaac Lab / IsaacGym style):
    #   from omni.isaac.lab.app import AppLauncher
    #   env = make_env(checkpoint_path, ...)
    #   policy = load_policy(checkpoint_path, ...)

    metrics = {}

    try:
        for cmd_name in commands:
            # NOTE: Reset environment with this command before the step loop.
            # Example: obs, _ = env.reset(command=cmd_name)

            episode_reward = 0.0
            success_count = 0
            total_steps = 0

            for _ in range(num_steps):
                # NOTE: Replace with framework-specific step logic.
                # Example:
                #   action = policy(obs)
                #   obs, reward, done, truncated, info = env.step(action)
                #   episode_reward += reward.item()
                #   if info.get("success"): success_count += 1
                #   total_steps += 1
                #   if done or truncated: break
                pass

            metrics[cmd_name] = {
                "episode_reward": episode_reward,
                "success_rate": success_count / max(total_steps, 1),
                "steps": total_steps,
            }

            # --- Task-specific quality metrics integration ---
            # When adapting this template, add trajectory collection in the scenario loop above:
            #   joint_pos_history.append(robot.data.joint_pos[0].cpu().numpy())
            #   contact_state_history.append(foot_contact[0].cpu().numpy())
            #   contact_force_history.append(foot_force[0].cpu().numpy())
            #
            # Then call the task's eval_metrics after each scenario:
            #   eval_mod = load_task_eval_metrics(config_path)
            #   if eval_mod:
            #       quality = eval_mod.analyze_trajectory(
            #           np.array(joint_pos_history), np.array(joint_vel_history),
            #           np.array(contact_state_history), np.array(contact_force_history), dt
            #       )
            #       metrics[cmd_name]["quality"] = quality
            #       quality_lines = eval_mod.format_markdown(quality, cmd_name)

    except Exception as e:
        print(f"ERROR: Evaluation failed: {e}", file=sys.stderr)
        sys.exit(1)

    lines = ["# Policy Evaluation Report", ""]
    for cmd_name, m in metrics.items():
        lines.append(f"## {cmd_name}")
        lines.append(f"- **Episode reward**: {m['episode_reward']:.4f}")
        lines.append(f"- **Success rate**: {m['success_rate']:.2%}")
        lines.append(f"- **Steps**: {m['steps']}")
        lines.append("")

    raw_json = json.dumps(metrics)
    lines.append(f"<!-- RAW_METRICS:{raw_json}-->")

    report = "\n".join(lines)
    print(report)

    if output_path:
        Path(output_path).write_text(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", help="Path to policy checkpoint")
    parser.add_argument("--config", required=True, help="Path to eval config file")
    parser.add_argument("--output", default=None, help="Write report to this file")
    args = parser.parse_args()

    evaluate(args.checkpoint, args.config, args.output)


if __name__ == "__main__":
    main()
