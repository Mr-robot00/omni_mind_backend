import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# This line is crucial! It forces Python to read the .env file in your root folder
load_dotenv()

# Grab the URL from the .env file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# If it can't find the .env file, crash loudly so we know!
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("🚨 DATABASE_URL is missing! Make sure your .env file is saved in the root folder.")

# --- ADD THIS NEW FIX HERE ---
# SQLAlchemy requires 'postgresql://' but some cloud providers give 'postgres://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)
# -----------------------------

# Notice we removed the SQLite-specific 'check_same_thread' argument!
# Neon handles multiple threads automatically.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()