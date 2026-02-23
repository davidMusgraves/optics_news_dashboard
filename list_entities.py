from db.article_model import get_session, ArticleEntity
from collections import Counter


def list_entities(limit=20):
    session = get_session()
    entities = session.query(ArticleEntity).all()
    counts = Counter((e.name.strip(), e.type) for e in entities)

    print(f"\nTop {limit} extracted entities:\n")
    for (name, label), count in counts.most_common(limit):
        print(f"{name} ({label}): {count}")


if __name__ == "__main__":
    list_entities()
