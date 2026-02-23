import csv
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.article_model import get_session, Article, ArticleEntity

session = get_session()
joined = session.query(ArticleEntity, Article).join(Article).all()

os.makedirs("data", exist_ok=True)
with open("data/entity_annotation_dataset.csv", "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        "article_id", "entity", "predicted_type", "title", "summary", "source", "published", "corrected_type"
    ])
    writer.writeheader()

    for entity, article in joined:
        writer.writerow({
            "article_id": article.id,
            "entity": entity.name,
            "predicted_type": entity.type,
            "title": article.title,
            "summary": article.summary,
            "source": article.source,
            "published": article.published,
            "corrected_type": ""
        })

print("✅ Exported entities to data/entity_annotation_dataset.csv")
