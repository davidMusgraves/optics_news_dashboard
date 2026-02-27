# scripts/process_articles.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.db.article_model import get_session, Article, ArticleEntity
from digester.categorizer import categorize_article
from digester.entity_extractor import extract_entities

# Simple heuristics to guess your taxonomy
UNI_HINTS = ("University", "College", "Institute of", "Polytechnic", "École", "Technological University")
GOV_LAB_HINTS = (
    "Laboratory", "National Lab", "National Laboratory",
    "Lawrence Livermore", "Los Alamos", "Oak Ridge", "Argonne", "NIST", "NASA",
)
RESEARCH_GROUP_HINTS = ("Group", "Lab", "Center for", "Centre for", "Laboratory for")

def guess_custom_label(name: str, raw_label: str) -> str:
    n = (name or "").strip()
    if raw_label == "PERSON":
        return "PERSON"
    if raw_label in {"GPE", "NORP", "FAC"}:
        return raw_label

    # Sub-typing ORG:
    low = n.lower()
    if any(h.lower() in low for h in UNI_HINTS):
        return "UNIVERSITY"
    if any(h.lower() in low for h in GOV_LAB_HINTS):
        return "GOV_LAB"
    if any(h.lower() in low for h in RESEARCH_GROUP_HINTS):
        return "RESEARCH_GROUP"

    return "COMPANY"  # default bucket for remaining org-like entities

def process_unprocessed_articles(batch_limit=500):
    session = get_session()

    # Articles missing tags or whose entities haven't been created yet (simple heuristic)
    to_process = session.query(Article).filter((Article.tags == None) | (Article.tags == "")).limit(batch_limit).all()  # noqa: E711

    processed = 0
    for article in to_process:
        try:
            # Categorize (uses your existing keywords)
            article_dict = {
                "title": article.title or "",
                "summary": article.summary or "",
                "content": article.content or "",
                "source": article.source or "",
            }
            tags = categorize_article(article_dict)
            article.tags = ",".join(tags)

            # Prefer full content over summary for NER
            text = f"{article.title or ''}\n{article.content or article.summary or ''}"
            ents = extract_entities(text)

            # idempotent replace of entities
            session.query(ArticleEntity).filter_by(article_id=article.id).delete()

            for ent in ents:
                raw = ent["raw_label"]
                custom = guess_custom_label(ent["text"], raw)
                session.add(ArticleEntity(
                    article_id=article.id,
                    name=ent["text"],
                    raw_label=raw,
                    custom_label=custom,
                    type=raw  # keep legacy in sync for now
                ))

            session.commit()
            processed += 1
            print(f"[Process] Article {article.id}: {len(ents)} entities")
        except Exception as ex:
            session.rollback()
            print(f"[Error] Article {article.id}: {ex}")

    print(f"[Done] Processed {processed} articles.")

if __name__ == "__main__":
    process_unprocessed_articles()
