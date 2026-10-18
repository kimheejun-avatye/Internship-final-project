"""Run migrations against PostgreSQL configured by the root .env file."""

import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, pool


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

required = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_PORT")
missing = [name for name in required if not os.environ.get(name)]
if missing:
    raise RuntimeError("Set required variables in root .env: " + ", ".join(missing))

url = URL.create(
    "postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="127.0.0.1",
    port=int(os.environ["POSTGRES_PORT"]),
    database=os.environ["POSTGRES_DB"],
)

if context.is_offline_mode():
    context.configure(url=url, literal_binds=True, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
