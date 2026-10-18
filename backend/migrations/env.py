from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401

url = settings.database_url
if context.is_offline_mode():
    context.configure(url=url, literal_binds=True, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
