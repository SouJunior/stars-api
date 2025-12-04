from sqlalchemy import create_engine, text
from app.settings import settings

SQLALCHEMY_DATABASE_URL = (
    f"{settings.DB_DRIVER}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Dropping volunteer_status_history...")
        connection.execute(text("DROP TABLE IF EXISTS volunteer_status_history"))
        
        print("Dropping volunteer_status...")
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0;")) # Disable FK checks to allow dropping referenced table if needed
        connection.execute(text("DROP TABLE IF EXISTS volunteer_status"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

        print("Dropping index ix_items_title from items...")
        try:
            connection.execute(text("DROP INDEX ix_items_title ON items"))
        except Exception as e:
            print(f"Index drop failed (might not exist): {e}")
            
        print("Cleanup complete. You can now run alembic upgrade head.")
except Exception as e:
    print("Error during cleanup:", e)