# streamlit_app/pages/01_Entity_Label_Correction.py

# --- bootstrap import path BEFORE anything else that depends on it ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # .../optics_news_digester
sys.path.insert(0, str(ROOT))
# --------------------------------------------------------------------

import re
import pandas as pd
import streamlit as st
from sqlalchemy.orm import joinedload

from data.db.article_model import get_session, ArticleEntity, Article

CUSTOM_TYPES = [
    "PERSON", "COMPANY", "UNIVERSITY", "RESEARCH_GROUP", "GOV_LAB",
    "GPE", "NORP", "FAC", "OTHER", "IGNORE"
]

st.set_page_config(page_title="Entity Label Correction", layout="wide")
st.title("🧠 Named Entity Label Correction Tool")

def extract_context(entity_text: str, full_text: str, window_chars: int = 200) -> str:
    if not full_text:
        return "No text available."
    pattern = re.compile(re.escape(entity_text), flags=re.IGNORECASE)
    m = pattern.search(full_text)
    if not m:
        return "Not found in text"
    start = max(m.start() - window_chars, 0)
    end = min(m.end() + window_chars, len(full_text))
    snippet = full_text[start:end]
    highlighted = pattern.sub(lambda _: f"**🟡{entity_text}**", snippet)
    return highlighted

@st.cache_data
def load_pairs():
    session = get_session()
    results = (
        session.query(ArticleEntity, Article)
        .join(Article)
        .options(joinedload(ArticleEntity.article))
        .all()
    )
    return results

pairs = load_pairs()

rows = []
for ent, art in pairs:
    base_text = (getattr(art, "content", None) or art.summary or "")
    full_text = f"{(art.title or '').strip()}\n{base_text.strip()}"
    rows.append({
        "Entity ID": ent.id,
        "Entity Name": ent.name,
        "Raw (spaCy)": ent.raw_label or ent.type or "",
        "Custom Label": ent.custom_label or "",
        "Entity Context": extract_context(ent.name, full_text),
        "Title": art.title,
        "Source": art.source,
        "Link": art.link,
        "Published": art.published,
    })

df = pd.DataFrame(rows)
if df.empty:
    st.warning("⚠️ No entities found. Fetch & process articles, then reload.")
    st.stop()

st.sidebar.title("Filters")
st.sidebar.info(f"Loaded {len(df)} entity rows.")

# Filter by raw label (spaCy) or custom label
raw_opts = sorted([x for x in df["Raw (spaCy)"].dropna().unique().tolist() if x])
raw_sel = st.sidebar.multiselect("Filter by Raw (spaCy)", options=raw_opts, default=raw_opts)

custom_opts = sorted([x for x in df["Custom Label"].dropna().unique().tolist() if x] or CUSTOM_TYPES)
custom_sel = st.sidebar.multiselect("Filter by Custom Label", options=custom_opts, default=custom_opts)

text_filter = st.sidebar.text_input("Search (entity/title/source)")

mask = pd.Series([True] * len(df))
if raw_sel:
    mask &= df["Raw (spaCy)"].isin(raw_sel)
if custom_sel:
    mask &= df["Custom Label"].replace("", "OTHER").isin(custom_sel)  # treat empty as OTHER for filtering
if text_filter:
    t = text_filter.lower()
    mask &= df.apply(
        lambda r: t in (r.get("Entity Name", "") or "").lower()
               or t in (r.get("Title", "") or "").lower()
               or t in (r.get("Source", "") or "").lower(),
        axis=1
    )

df_view = df[mask].copy()

edited = st.data_editor(
    df_view,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Custom Label": st.column_config.SelectboxColumn(options=CUSTOM_TYPES),
        "Link": st.column_config.LinkColumn(),
    },
    disabled=[
        "Entity ID", "Entity Name", "Raw (spaCy)",
        "Entity Context", "Title", "Source", "Link", "Published"
    ],
    key="entity_editor"
)

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Save Corrections to CSV"):
        out = "data/label_corrections.csv"
        edited.to_csv(out, index=False)
        st.success(f"Saved to {out}")

with col2:
    if st.button("🗄️ Save Custom Labels to DB"):
        session = get_session()
        updated = 0
        for _, row in edited.iterrows():
            eid = row["Entity ID"]
            new_label = row["Custom Label"] or None
            ent = session.query(ArticleEntity).get(eid)
            if ent and ent.custom_label != new_label:
                ent.custom_label = new_label
                session.add(ent)
                updated += 1
        session.commit()
        st.success(f"Updated {updated} rows in the database.")

st.markdown("### 🔍 Entity Context Viewer")
for _, row in edited.iterrows():
    with st.expander(f"{row['Entity Name']} — {row['Title']}"):
        st.markdown(f"**Raw (spaCy)**: {row['Raw (spaCy)']}")
        st.markdown(f"**Custom Label**: {row['Custom Label'] or '—'}")
        st.markdown(f"**Source**: {row['Source']} — {row['Published']}")
        if row.get("Link"):
            st.markdown(f"[🔗 View original]({row['Link']})")
        st.markdown("**Context:**")
        st.markdown(row["Entity Context"])
