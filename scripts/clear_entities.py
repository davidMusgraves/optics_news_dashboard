import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from db.article_model import get_session, ArticleEntity

session = get_session()
deleted_count = session.query(ArticleEntity).delete()
session.commit()
print(f"✅ Deleted {deleted_count} ArticleEntity entries.")
