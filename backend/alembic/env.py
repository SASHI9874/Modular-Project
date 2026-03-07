from dotenv import load_dotenv
load_dotenv()
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.db.base_class import Base

# Import ALL models so Alembic can detect them
from app.entities.user_entity import User
from app.entities.feature_entity import FeatureEntity
from app.entities.project_entity import ProjectEntity

print("ALEMBIC DATABASE URL =", settings.SQLALCHEMY_DATABASE_URI)
config = context.config

# Force Alembic to use DATABASE_URL from settings
database_url = settings.SQLALCHEMY_DATABASE_URI
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
