# LangSmith CLI (team setup)

Scriptable access to traces, runs, datasets — useful for debugging and coding agents.

## Install

```bash
curl -fsSL https://cli.langsmith.com/install.sh | sh
# or: scripts/install_langsmith_cli.sh
```

## Auth (cloud)

```bash
langsmith auth login
# headless: langsmith auth login --no-browser --workspace-id <id>
```

Or API key:

```bash
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="dell-capstone-adaptive-exp-agent"
```

## Quick commands

```bash
langsmith project list
langsmith trace list --project dell-capstone-adaptive-exp-agent --limit 5
langsmith trace get <trace-id> --project dell-capstone-adaptive-exp-agent --full
langsmith run list --project dell-capstone-adaptive-exp-agent --run-type llm
```

Pretty tables: `langsmith --format pretty trace list --project ...`

## Sandboxes (LangSmith)

```bash
langsmith sandbox list
```

For code execution in agents we use **local sandbox** (`src/tools/sandbox_local.py`) in v2; remote LangSmith/Daytona sandboxes can replace it later.
