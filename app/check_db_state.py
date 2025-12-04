from sqlalchemy import create_engine, inspect, text
from app.settings import settings

SQLALCHEMY_DATABASE_URL = (
    f"{settings.DB_DRIVER}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables in database:", tables)

    if 'volunteer' in tables:
        columns = [c['name'] for c in inspector.get_columns('volunteer')]
        print(f"Volunteer columns: {columns}")
    
    if 'items' in tables:
        columns = [c for c in inspector.get_columns('items') if c['name'] == 'description']
        print(f"Items description column: {columns}")
        indexes = [i['name'] for i in inspector.get_indexes('items')]
        print(f"Items indexes: {indexes}")

    with engine.connect() as connection:
        try:
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print("Current Alembic Version:", version)
        except Exception as e:
            print("Could not read alembic_version:", e)
except Exception as e:
    print("Error connecting to DB:", e)
