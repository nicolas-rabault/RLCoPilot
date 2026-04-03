# RLCoPilot — Developer Instructions

## Versioning

The plugin version lives in `.claude-plugin/plugin.json` (`"version"` field). **Bump the version on every user-facing change** — this is what triggers update detection for installed users.

Use semver:
- **patch** (0.1.0 → 0.1.1): bug fixes, wording changes
- **minor** (0.1.0 → 0.2.0): new features, new skill phases
- **major** (0.1.0 → 1.0.0): breaking changes to config format or skill interface
