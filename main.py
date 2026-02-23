# main.py
from digester.categorizer import categorize_article
from digester.entity_extractor import extract_entities
from db.article_model import get_session, Article, ArticleEntity
from sqlalchemy.exc import IntegrityError


def process_unprocessed_articles(batch_size=200):
    session = get_session()

    # find articles with missing tags OR missing entities
    q = session.query(Article).filter((Article.tags == None) | (Article.tags == ""))  # noqa: E711
    to_process = q.limit(batch_size).all()

    processed = 0
    for article in to_process:
        try:
            # categorize
            article_dict = {
                "title": article.title or "",
                "summary": article.summary or "",
                "content": article.content or "",
                "source": article.source or "",
            }
            tags = categorize_article(article_dict)
            article.tags = ",".join(tags)

            # extract entities using full text if present
            text = f"{article.title or ''}\n{article.content or article.summary or ''}"
            ents = extract_entities(text)
            # clear any existing entities for this article (idempotent)
            session.query(ArticleEntity).filter_by(article_id=article.id).delete()
            for ent in ents:
                session.add(ArticleEntity(article_id=article.id, name=ent["text"], type=ent["label"]))

            session.commit()
            processed += 1
        except IntegrityError:
            session.rollback()
        except Exception as ex:
            session.rollback()
            print(f"[Process] Failed for article {article.id}: {ex}")

    print(f"[Process] Processed {processed} articles.")


if __name__ == "__main__":
    process_unprocessed_articles()
