#!/usr/bin/env bash
# Install or upgrade LangSmith CLI (opt-in; not required for pytest).
set -euo pipefail
curl -fsSL https://cli.langsmith.com/install.sh | sh
langsmith --version || true
echo "Then: langsmith auth login"
