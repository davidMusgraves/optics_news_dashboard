#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

source .venv/bin/activate
mkdir -p logs
/Users/jdmusgraves/Projects/optics_news_dashboard/.venv/bin/python scripts/run_fetcher.py --limit 5 >> logs/ingest.log 2>&1
echo "Ingest done. See logs/ingest.log"