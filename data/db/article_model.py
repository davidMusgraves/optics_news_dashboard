# db/article_model.py
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String, unique=True, index=True)
    summary = Column(Text)
    content = Column(Text)               # full article text
    published = Column(String)
    source = Column(String)
    tags = Column(String)                # comma-separated
    fetched_at = Column(DateTime, default=datetime.utcnow)

    entities = relationship("ArticleEntity", back_populates="article", cascade="all, delete-orphan")
    labels = relationship("ArticleLabel", backref="article", cascade="all, delete-orphan")  # optional (article-level tags)
    span_annotations = relationship("ArticleSpanAnnotation", back_populates="article", cascade="all, delete-orphan")

class ArticleEntity(Base):
    __tablename__ = "article_entities"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    name = Column(String)

    # legacy + explicit NER fields
    type = Column(String)          # (legacy) spaCy label if you used it
    raw_label = Column(String)     # spaCy label
    custom_label = Column(String)  # your taxonomy (COMPANY, UNIVERSITY, ...)

    article = relationship("Article", back_populates="entities")

class ArticleLabel(Base):
    __tablename__ = "article_labels"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), index=True)
    label = Column(String, index=True)   # e.g., LIDAR, MATERIALS, ...

    __table_args__ = (UniqueConstraint('article_id', 'label', name='_article_label_uc'),)

# NEW: human span annotations (character offsets in the article text)
class ArticleSpanAnnotation(Base):
    __tablename__ = "article_span_annotations"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), index=True)

    start_char = Column(Integer, index=True)  # inclusive
    end_char = Column(Integer, index=True)    # exclusive
    label = Column(String, index=True)        # e.g., PERSON, COMPANY, UNIVERSITY, GOV_LAB, ...
    text = Column(String)                     # denormalized convenience copy of the span text

    annotator = Column(String, default="manual")  # optional: who annotated (or "manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="span_annotations")

def get_session(db_path="sqlite:///data/articles.db"):
    engine = create_engine(db_path)

    # Light auto-migration helpers for SQLite dev. In production, use alembic.
    with engine.begin() as conn:
        # articles columns we added earlier
        try: conn.exec_driver_sql("ALTER TABLE articles ADD COLUMN content TEXT")
        except Exception: pass
        try: conn.exec_driver_sql("ALTER TABLE articles ADD COLUMN fetched_at DATETIME")
        except Exception: pass
        # article_entities columns (raw/custom labels)
        try: conn.exec_driver_sql("ALTER TABLE article_entities ADD COLUMN raw_label VARCHAR")
        except Exception: pass
        try: conn.exec_driver_sql("ALTER TABLE article_entities ADD COLUMN custom_label VARCHAR")
        except Exception: pass
        # Ensure span annotation table exists
        # (create_all will create the table if missing)
        pass

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
