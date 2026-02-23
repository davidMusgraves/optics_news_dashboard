# scripts/migrate_entity_labels.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from db.article_model import Base

def column_exists(conn, table, column):
    rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)

def main():
    engine = create_engine("sqlite:///data/articles.db")
    with engine.begin() as conn:
        if not column_exists(conn, "article_entities", "raw_label"):
            print("[migrate] Add article_entities.raw_label")
            conn.exec_driver_sql("ALTER TABLE article_entities ADD COLUMN raw_label VARCHAR")
        if not column_exists(conn, "article_entities", "custom_label"):
            print("[migrate] Add article_entities.custom_label")
            conn.exec_driver_sql("ALTER TABLE article_entities ADD COLUMN custom_label VARCHAR")
    Base.metadata.create_all(engine)
    print("✅ Migration complete.")

if __name__ == "__main__":
    main()
