import streamlit as st
from collections import Counter
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data.db.article_model import get_session, ArticleEntity, Article

st.set_page_config(page_title="Optics & Photonics Entity Dashboard", layout="wide")
st.title("Named Entity Frequency in Optics & Photonics News")

# Sidebar filters
st.sidebar.title("Filters")
top_n = st.sidebar.slider("Top N entities", min_value=5, max_value=50, value=20)


@st.cache_data
def load_entity_data():
    session = get_session()
    entities = session.query(ArticleEntity).all()
    return [(e.name.strip(), e.type) for e in entities]


data = load_entity_data()

# Frequency aggregation
counter = Counter(data)
df = pd.DataFrame(counter.items(), columns=["Entity", "Count"])
df[["Name", "Type"]] = pd.DataFrame(df["Entity"].tolist(), index=df.index)
df = df[["Name", "Type", "Count"]].sort_values("Count", ascending=False)

# Filter by type
entity_types = sorted(df["Type"].unique())
selected_types = st.sidebar.multiselect("Entity Types", entity_types, default=entity_types)
filtered_df = df[df["Type"].isin(selected_types)]

# Chart
st.bar_chart(filtered_df.head(top_n).set_index("Name")["Count"])

with st.expander("📋 Show Full Table"):
    st.dataframe(filtered_df.reset_index(drop=True))

with st.expander("🕵️ Audit Entities by Article"):
    session = get_session()
    joined = session.query(ArticleEntity, Article).join(Article).all()

    audit_rows = []
    for entity, article in joined:
        audit_rows.append({
            "Entity": entity.name,
            "Type": entity.type,
            "Article Title": article.title,
            "Source": article.source,
            "Published": article.published
        })

    audit_df = pd.DataFrame(audit_rows)
    st.dataframe(audit_df)
