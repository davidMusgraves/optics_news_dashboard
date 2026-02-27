#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

source .venv/bin/activate
echo "Python: $(python --version)"
echo "DB exists? $(test -f data/articles.db && echo yes || echo no)"
echo "Recent logs:"
ls -l logs/*.log 2>/dev/null || echo "No logs yet"