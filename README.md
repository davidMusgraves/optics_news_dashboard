# Optics & Photonics News Dashboard

Automated news digester and named-entity tracker for optics, photonics, and LiDAR.
Fetches from 30 RSS feeds, runs spaCy NER, and surfaces entities in a Streamlit dashboard.

---

## Quick start (local)

```bash
# 1. Create a virtual environment and install deps
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — the SQLite default works out of the box for local dev

# 3. Fetch articles and extract entities
python scripts/run_fetcher.py
python scripts/process_articles.py

# 4. Launch the dashboard
streamlit run streamlit_app/Home.py
```

---

## Deploying to production

### Step 1 — Create a Supabase database

1. Sign up at [supabase.com](https://supabase.com) (free tier is sufficient).
2. Create a new project.
3. Go to **Settings → Database → Connection string → URI** and copy the URI.
   It looks like: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
4. The first time you run the app (or any script) against the Postgres URL,
   SQLAlchemy will auto-create all tables via `Base.metadata.create_all()`.

> **Migrating existing data:** If you want to carry over your local SQLite data,
> use `pgloader` or export/import with pandas. For a fresh start just leave it.

---

### Step 2 — Push to GitHub

```bash
cd optics_news_dashboard
git init
git add .
git commit -m "Initial commit"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR-USERNAME/optics-news-dashboard.git
git push -u origin main
```

---

### Step 3 — Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repo and set **Main file path** to:
   ```
   streamlit_app/Home.py
   ```
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   DATABASE_URL = "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
   ```
   (See `.streamlit/secrets.toml.example` for the full template.)
5. Click **Deploy**. Streamlit Cloud will install `packages.txt` then `requirements.txt`
   automatically and start the app.

---

### Step 4 — Set up automated ingestion (GitHub Actions)

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**.
2. Add a repository secret:
   - **Name:** `DATABASE_URL`
   - **Value:** your Supabase connection string
3. That's it. The workflow at `.github/workflows/ingest.yml` will run every 6 hours,
   fetching new articles and processing entities automatically.
   You can also trigger it manually from the **Actions** tab.

---

## Project structure

```
optics_news_dashboard/
├── config/
│   └── sources.yaml          # RSS feed list
├── data/
│   └── db/
│       └── article_model.py  # SQLAlchemy ORM + get_session()
├── digester/
│   ├── rss_fetcher.py
│   ├── entity_extractor.py   # spaCy NER + custom ruler
│   └── categorizer.py        # keyword-based tagging
├── scripts/
│   ├── run_fetcher.py        # ingest pipeline entry point
│   └── process_articles.py   # categorise + extract entities
├── streamlit_app/
│   ├── Home.py               # main entry point (Streamlit Cloud points here)
│   └── pages/
│       ├── 01_Entity_Label_Correction.py
│       ├── 02_Entity_Dashboard.py
│       └── 04_Span_Annotator.py
├── .github/
│   └── workflows/
│       └── ingest.yml        # scheduled ingestion (every 6 h)
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── packages.txt              # apt packages for Streamlit Cloud
└── requirements.txt
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes (production) | SQLAlchemy-compatible DB URL. SQLite default used locally. |
| `OPENAI_API_KEY` | No | For future LLM summarisation |
| `ANTHROPIC_API_KEY` | No | For future LLM summarisation |
| `ENABLE_SPACY_NER` | No | Toggle spaCy NER (default: `true`) |
| `FETCH_FULLTEXT` | No | Toggle full-text scraping (default: `true`) |
