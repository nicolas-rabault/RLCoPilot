---
name: discord-notify
description: Sets up and manages Discord webhook notifications for Claude Code projects. Use this skill whenever starting work on a project that has a CLAUDE.md but might not have Discord notifications configured yet. Also use when you need to send a notification to the user via Discord — for task completion, errors, blockers, or any message another skill or hook wants to push. Trigger this whenever you see a project without a .claude-discord.md file, when completing a major task, when hitting a blocker, or when any part of the system wants to notify the user.
---

# Discord Notify

This skill connects Claude Code projects to Discord so the user gets notified about important events (task completion, errors, blockers) without watching the terminal.

## Architecture

Each project gets a dedicated Discord text channel with a webhook. The webhook URL is stored locally in `.claude-discord.md` at the project root — this file is gitignored so credentials never leak to version control.

```
Project root/
├── CLAUDE.md              ← references .claude-discord.md via @import
├── .claude-discord.md     ← webhook URL + notification instructions (gitignored)
└── .gitignore             ← includes .claude-discord.md
```

## Setup Flow

When you detect a project with `CLAUDE.md` but no `.claude-discord.md`:

### Step 1: Ask the user to create a Discord channel

Tell the user:

> I'd like to set up Discord notifications for this project. Please:
> 1. Open your Discord server
> 2. Create a new **text channel** named after this project (e.g., `#project-name`)
> 3. Go to **Channel Settings > Integrations > Webhooks**
> 4. Click **New Webhook**, give it a name like "Claude Code", and copy the webhook URL
> 5. Paste the webhook URL here

### Step 2: Store the webhook configuration

Once the user provides the webhook URL, create `.claude-discord.md` at the project root:

```markdown
---
name: Discord Notifications
description: Discord webhook configuration for this project. DO NOT commit this file.
---

## Discord Webhook

WEBHOOK_URL: <the-url-the-user-provided>

## When to Notify

Send a Discord notification in these situations:
- **Task completion**: When you finish a significant task the user asked for
- **Error or blocker**: When you hit something that blocks progress and needs the user's attention
- **On request**: When another skill, hook, or the user explicitly asks to send a Discord message

## How to Send a Notification

Use this exact bash command (replace MESSAGE with your content):

\```bash
curl -s -H "Content-Type: application/json" \
  -d '{"content":"MESSAGE"}' \
  WEBHOOK_URL
\```

Keep messages concise (under 2000 chars — Discord's limit). Use Discord markdown:
- **bold** for emphasis
- `code` for file names and commands
- ```language for code blocks

### Message Format

For task completion:
\```
**Task Complete** — <short summary>
Project: <project-name>
\```

For errors/blockers:
\```
**Blocker** — <what's wrong>
Project: <project-name>
Action needed: <what the user should do>
\```

For general messages:
\```
<your message>
Project: <project-name>
\```
```

Replace `WEBHOOK_URL` in both places (the config line and the curl command) with the actual URL the user provided, and `<project-name>` with the actual project directory name.

### Step 3: Update .gitignore

Check if `.gitignore` exists and whether it already contains `.claude-discord.md`. If not, append:

```
# Discord webhook config (contains secrets)
.claude-discord.md
```

### Step 4: Update CLAUDE.md

Add this line to the project's `CLAUDE.md` (at the top, near other `@` imports if any):

```
@.claude-discord.md
```

This ensures every Claude session in the project automatically loads the webhook config.

### Step 5: Send a test notification

Send a test message to confirm the webhook works:

```bash
curl -s -H "Content-Type: application/json" \
  -d '{"content":"**Connected** — Claude Code is now linked to this channel.\nProject: <project-name>"}' \
  <webhook-url>
```

If the curl returns an error or the user doesn't see the message, troubleshoot with them.

## Sending Notifications (for other skills and hooks)

When `.claude-discord.md` is already configured and loaded via CLAUDE.md, sending a notification is straightforward — just read the webhook URL from the loaded config and use the curl command documented there. The config file contains message format templates.

If you want to notify but aren't sure if Discord is set up, check for `.claude-discord.md` in the project root first. If it doesn't exist, run the setup flow above.
