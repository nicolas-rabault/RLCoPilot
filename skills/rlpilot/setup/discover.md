# SETUP-DISCOVER

You are setting up RL training configuration for this project. Your job is to scan the codebase, identify the RL training setup, and gather robot/objective details from the user.

## Step 1: Codebase Exploration (autonomous)

No user interaction. Scan the project:
- Read project structure, dependencies (`pyproject.toml`, `setup.py`, `requirements.txt`), entry points
- Identify: simulator, RL framework, algorithm, task names
- Look at existing training scripts, config files, reward definitions
- Produce a findings summary for the next steps

## Step 2: Robot & Objective (interactive)

Present findings from Step 1. Ask user to confirm or correct. Then ask (one question at a time):
- Robot type and key physical traits / constraints
- Actuated joints and any special mechanics
- Training objective — what should the robot learn?

## Output

Write `.claude/rl-training/config.md` with these sections (use the template below as a starting point):

```
## Robot
- Name: <robot name>
- Type: <biped, quadruped, arm, etc.>
- Specificities: <key physical traits, constraints>
- Actuators: [<joint1>, <joint2>, ...]
- Special mechanics: <any special mechanisms, conversions>

## Task
- Name: <task identifier>
- Simulator: <MuJoCo, IsaacSim, PyBullet, etc.>
- Framework: <mjlab, IsaacLab, etc.>
- Algorithm: <PPO, SAC, etc.>
- Objective: <what the robot should learn>

## Training
- Command: <full training command>
- Execution: <remote or local>
- Env count: <number of parallel environments>

## Source Files
- Task config: <path>
- Rewards: <path>
- Observations: <path>
```

Create the `.claude/rl-training/` directory if it doesn't exist.
