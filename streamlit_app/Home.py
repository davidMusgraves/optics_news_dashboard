# streamlit_app/Home.py  — main entry point for Streamlit Cloud
#
# This file must be the one you point Streamlit Cloud at:
#   Main file path: streamlit_app/Home.py
#
# It also bridges st.secrets → os.environ so that every page and every
# script (run_fetcher, process_articles) can call os.environ["DATABASE_URL"]
# regardless of whether they're running on Streamlit Cloud or in CI.

import os
import sys
from pathlib import Path

# ── import path ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent   # project root
sys.path.insert(0, str(ROOT))

# ── secrets bridge ───────────────────────────────────────────────────────────
# On Streamlit Cloud, secrets live in st.secrets.
# Expose them as env vars so article_model.get_session() and scripts can find them.
import streamlit as st

_SECRET_KEYS = ["DATABASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "NEWS_API_KEY"]
for _k in _SECRET_KEYS:
    if _k in st.secrets and not os.environ.get(_k):
        os.environ[_k] = st.secrets[_k]

# ── page ─────────────────────────────────────────────────────────────────────
from data.db.article_model import get_session, Article, ArticleEntity

st.set_page_config(
    page_title="Optics & Photonics Dashboard",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 Optics & Photonics News Dashboard")
st.caption("Named-entity tracking across optics, photonics, and LiDAR news sources.")

st.divider()

# ── quick stats ──────────────────────────────────────────────────────────────
try:
    session = get_session()
    n_articles = session.query(Article).count()
    n_entities = session.query(ArticleEntity).count()
    n_sources  = session.query(Article.source).distinct().count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Articles ingested", f"{n_articles:,}")
    col2.metric("Entity mentions", f"{n_entities:,}")
    col3.metric("News sources", n_sources)
    session.close()
except Exception as e:
    st.warning(f"Could not connect to the database: {e}")

st.divider()

st.markdown("""
### Pages

| Page | What it does |
|------|-------------|
| **Entity Dashboard** | Bar charts of the most-mentioned organisations, people, and labs |
| **Label Correction** | Review and correct the spaCy-predicted entity taxonomy labels |
| **Span Annotator** | Create character-level ground-truth spans for model training |

Use the sidebar to navigate between pages.
""")

st.markdown("""
### Pipeline

New articles are ingested automatically every 6 hours via GitHub Actions.
To run the pipeline manually:

```bash
python scripts/run_fetcher.py
python scripts/process_articles.py
```
""")
