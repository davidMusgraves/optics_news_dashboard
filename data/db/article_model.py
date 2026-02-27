# db/article_model.py
import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    labels = relationship("ArticleLabel", backref="article", cascade="all, delete-orphan")
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

class ArticleSpanAnnotation(Base):
    __tablename__ = "article_span_annotations"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), index=True)

    start_char = Column(Integer, index=True)  # inclusive
    end_char = Column(Integer, index=True)    # exclusive
    label = Column(String, index=True)
    text = Column(String)                     # denormalized convenience copy

    annotator = Column(String, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="span_annotations")


def _resolve_db_url():
    """
    Resolve the database URL with this priority:
      1. DATABASE_URL environment variable (set by GitHub Actions, local .env, or
         injected by the Streamlit Cloud secrets bridge in Home.py)
      2. Legacy DB_SQLALCHEMY_URL env var (backwards compat)
      3. Default SQLite path for local development
    """
    url = os.environ.get("DATABASE_URL") or os.environ.get("DB_SQLALCHEMY_URL")
    if not url:
        url = "sqlite:///data/articles.db"
    # Supabase / Heroku ship postgres:// URIs; SQLAlchemy 1.4+ requires postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_session(db_url=None):
    if db_url is None:
        db_url = _resolve_db_url()

    is_sqlite = db_url.startswith("sqlite")
    engine_kwargs = {}
    if not is_sqlite:
        # Keep connections alive across Streamlit reruns
        engine_kwargs["pool_pre_ping"] = True

    engine = create_engine(db_url, **engine_kwargs)

    # SQLite-only: light schema migrations for dev convenience.
    # On Postgres use Alembic (or run create_all on first deploy).
    if is_sqlite:
        with engine.begin() as conn:
            for stmt in [
                "ALTER TABLE articles ADD COLUMN content TEXT",
                "ALTER TABLE articles ADD COLUMN fetched_at DATETIME",
                "ALTER TABLE article_entities ADD COLUMN raw_label VARCHAR",
                "ALTER TABLE article_entities ADD COLUMN custom_label VARCHAR",
            ]:
                try:
                    conn.exec_driver_sql(stmt)
                except Exception:
                    pass  # column already exists

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
