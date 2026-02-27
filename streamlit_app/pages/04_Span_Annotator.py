# streamlit_app/pages/04_Span_Annotator.py

# --- bootstrap path ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
# ----------------------

import re
import streamlit as st
from data.db.article_model import get_session, Article, ArticleSpanAnnotation
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
from html import escape

# Customize your taxonomy here (these are span labels)
SPAN_LABELS = [
    "PERSON", "COMPANY", "UNIVERSITY", "RESEARCH_GROUP", "GOV_LAB",
    "GPE", "NORP", "FAC", "OTHER",
]

st.set_page_config(page_title="Span-level NER Annotator", layout="wide")
st.title("✍️ Span-level Entity Annotator")

@st.cache_data
def list_article_ids():
    s = get_session()
    ids = [row[0] for row in s.query(Article.id).order_by(desc(Article.fetched_at), desc(Article.id)).all()]
    return ids

def find_occurrences(text: str, needle: str):
    """Return list of (start, end) indices for case-insensitive non-overlapping matches."""
    spans = []
    if not text or not needle:
        return spans
    pattern = re.compile(re.escape(needle), flags=re.IGNORECASE)
    for m in pattern.finditer(text):
        spans.append((m.start(), m.end()))
    return spans

def highlight_spans(text: str, highlights: list):
    """
    highlights: list of dicts with keys:
       - start, end (char offsets, exclusive end)
       - label (string)
       - color (string HEX or name)
    Returns HTML with <mark> wrappers for spans. Assumes non-overlapping.
    """
    if not text:
        return "<i>No text</i>"

    # sort by start asc
    highlights = sorted(highlights, key=lambda h: h["start"])
    out = []
    curr = 0
    for h in highlights:
        s, e = h["start"], h["end"]
        color = h.get("color", "#ffd54f")
        lab = h.get("label", "")
        # add plain segment
        if s > curr:
            out.append(escape(text[curr:s]))
        # add highlighted
        span_html = f'<mark style="background:{color}; padding:0 2px; border-radius:3px;" title="{escape(lab)}">{escape(text[s:e])}</mark>'
        out.append(span_html)
        curr = e
    # tail
    if curr < len(text):
        out.append(escape(text[curr:]))
    return "".join(out)

# Pick article
article_ids = list_article_ids()
if not article_ids:
    st.warning("No articles found. Fetch & process first.")
    st.stop()

idx = st.selectbox("Select article (newest first by fetched_at)", options=list(range(len(article_ids))), index=0)
article_id = article_ids[idx]

s = get_session()
article = s.query(Article).options(joinedload(Article.span_annotations)).get(article_id)
full_text = (article.content or article.summary or "")  # prefer full
st.subheader(article.title or "(untitled)")
st.caption(f"{article.source} — {article.published}")
if article.link:
    st.markdown(f"[🔗 Open original]({article.link})")
st.divider()

# Show current annotations as highlights
palette = ["#ffeb3b", "#a5d6a7", "#90caf9", "#f48fb1", "#ffe082", "#b39ddb", "#80deea"]
existing = article.span_annotations or []
existing_highlights = []
for i, ann in enumerate(existing):
    existing_highlights.append({
        "start": ann.start_char,
        "end": ann.end_char,
        "label": f"{ann.label}",
        "color": palette[i % len(palette)]
    })

html_preview = highlight_spans(full_text, existing_highlights)
st.markdown("**Preview (existing spans highlighted):**", unsafe_allow_html=True)
st.markdown(f"<div style='white-space:pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;'>{html_preview}</div>", unsafe_allow_html=True)
st.divider()

# Annotate via substring search
st.markdown("### 🔎 Annotate by searching a substring")
needle = st.text_input("Entity text (case-insensitive)")
occ_spans = find_occurrences(full_text, needle) if needle else []
if needle:
    st.caption(f"Found {len(occ_spans)} occurrence(s).")
occ_idx = st.number_input("Occurrence index (0-based)", min_value=0, max_value=max(0, len(occ_spans)-1), value=0, step=1, disabled=(len(occ_spans) == 0))

label = st.selectbox("Label", options=SPAN_LABELS, index=0)
annotator = st.text_input("Annotator (optional)", value="manual")

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add annotation (by substring)"):
        if not needle or not occ_spans:
            st.error("Enter an entity text and make sure it exists in the article.")
        else:
            start, end = occ_spans[int(occ_idx)]
            span_text = full_text[start:end]
            ann = ArticleSpanAnnotation(
                article_id=article.id,
                start_char=start,
                end_char=end,
                label=label,
                text=span_text,
                annotator=annotator or "manual"
            )
            s.add(ann)
            s.commit()
            st.success(f"Added span [{start}, {end}) → {label}")
            st.rerun()

with col2:
    with st.expander("✍️ Or annotate by manual character offsets"):
        start_char = st.number_input("start_char (inclusive)", min_value=0, max_value=max(0, len(full_text)), value=0, step=1)
        end_char = st.number_input("end_char (exclusive)", min_value=0, max_value=max(0, len(full_text)), value=0, step=1)
        if st.button("➕ Add annotation (by offsets)"):
            if end_char <= start_char or end_char > len(full_text):
                st.error("Invalid offsets.")
            else:
                span_text = full_text[start_char:end_char]
                ann = ArticleSpanAnnotation(
                    article_id=article.id,
                    start_char=int(start_char),
                    end_char=int(end_char),
                    label=label,
                    text=span_text,
                    annotator=annotator or "manual"
                )
                s.add(ann)
                s.commit()
                st.success(f"Added span [{start_char}, {end_char}) → {label}")
                st.rerun()

st.divider()
st.markdown("### 🗂️ Existing annotations")

if existing:
    for ann in existing:
        st.markdown(f"- **{ann.label}**: `{ann.text}`  [{ann.start_char}, {ann.end_char})  —  {ann.annotator} @ {ann.created_at}")
        if st.button(f"🗑️ Delete #{ann.id}", key=f"del_{ann.id}"):
            s.delete(ann)
            s.commit()
            st.success(f"Deleted annotation {ann.id}")
            st.rerun()
else:
    st.info("No span annotations yet for this article.")
