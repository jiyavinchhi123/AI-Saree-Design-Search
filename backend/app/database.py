import os
import json
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join("data", "saree_search.db")
os.makedirs("data", exist_ok=True)

# PostgreSQL support if DATABASE_URL is set, else SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserRecord(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True) # Microsoft account ID or email
    email = Column(String(255), index=True)
    display_name = Column(String(255))
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    selected_notebooks_json = Column(Text, default="[]") # JSON list of selected notebook IDs
    total_designs = Column(Integer, default=0)

class DesignRecord(Base):
    __tablename__ = "designs"

    id = Column(String(64), primary_key=True, index=True)
    design_id = Column(String(64), index=True)
    user_id = Column(String(64), index=True, nullable=True) # Tenant/User Isolation
    title = Column(String(255))
    notebook_name = Column(String(255), index=True)
    section_name = Column(String(255), index=True)
    page_title = Column(String(255))
    onenote_web_url = Column(Text, nullable=True)
    onenote_client_url = Column(Text, nullable=True)
    image_url = Column(String(512))
    structural_preview_url = Column(String(512), nullable=True)
    category = Column(String(128), default="Traditional")
    colorway = Column(String(128), nullable=True)
    motifs_json = Column(Text, default="[]")
    weave_type = Column(String(128), nullable=True)
    source_type = Column(String(64), default="demo_catalog")
    created_at = Column(DateTime, default=datetime.utcnow)

class SearchHistoryRecord(Base):
    __tablename__ = "search_history"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=True) # Tenant/User Isolation
    timestamp = Column(DateTime, default=datetime.utcnow)
    query_image_url = Column(String(512))
    query_structural_preview_url = Column(String(512), nullable=True)
    top_match_id = Column(String(64), nullable=True)
    top_match_title = Column(String(255), nullable=True)
    top_match_image_url = Column(String(512), nullable=True)
    similarity_percentage = Column(Float, default=0.0)
    is_strong_match = Column(Boolean, default=False)
    notebook_name = Column(String(255), nullable=True)
    section_name = Column(String(255), nullable=True)
    page_title = Column(String(255), nullable=True)
    onenote_web_url = Column(Text, nullable=True)

class SettingsRecord(Base):
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text)

Base.metadata.create_all(bind=engine)

def _migrate_sqlite_columns():
    """Safely adds missing columns to existing SQLite tables if not present."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check designs table columns
        cursor.execute("PRAGMA table_info(designs)")
        design_cols = [row[1] for row in cursor.fetchall()]
        if "user_id" not in design_cols:
            cursor.execute("ALTER TABLE designs ADD COLUMN user_id VARCHAR(64)")
            
        # Check search_history table columns
        cursor.execute("PRAGMA table_info(search_history)")
        history_cols = [row[1] for row in cursor.fetchall()]
        if "user_id" not in history_cols:
            cursor.execute("ALTER TABLE search_history ADD COLUMN user_id VARCHAR(64)")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Migration Note] {e}")

_migrate_sqlite_columns()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
