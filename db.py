from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL, DB_POOL_SETTINGS

# Create SQLAlchemy engine and session - PostgreSQL ONLY
engine = create_engine(DATABASE_URL, **DB_POOL_SETTINGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# (Optional) Test connection immediately
# (Optional) Test connection immediately
if __name__ == "__main__":
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ DB connected:", result.fetchone())
    except Exception as e:
        print("❌ DB connection failed:", e)
