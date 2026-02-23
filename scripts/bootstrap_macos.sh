#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[bootstrap] Project dir: $PROJECT_DIR"

mkdir -p data/raw data/processed data/db data/exports logs config tests
mkdir -p src/optics_news/{ingest,classify,digest,dashboard}

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install feedparser requests pyyaml python-dotenv sqlalchemy pandas streamlit spacy
python -m spacy download en_core_web_sm || true

touch data/db/optics_news.db
touch logs/ingest.log logs/classify.log logs/dashboard.log logs/cron.log

echo "[bootstrap] Done."