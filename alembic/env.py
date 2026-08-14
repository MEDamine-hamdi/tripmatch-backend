import os
import sys
from logging.config import fileConfig
from app.models.trip import Trip  # noqa: F401 — importé pour qu'Alembic voie le modèle
from app.models.reservation import Reservation  # noqa: F401 — importé pour qu'Alembic voie le modèle
from app.models.rating import Rating  # noqa: F401 — importé pour qu'Alembic voie le modèle

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.models.conversation import Conversation  # noqa: F401 — importé pour qu'Alembic voie le modèle
from app.models.message import Message  # noqa: F401 — importé pour qu'Alembic voie le modèle
from app.models.notification import Notification  # noqa: F401 — importé pour qu'Alembic voie le modèle  # noqa: F401 — importé pour qu'Alembic voie le modèle
from alembic import context

# Permet d'importer "app" depuis la racine du projet
sys.path.insert(0, os.getcwd())

from app.core.config import settings
from app.db.session import Base
from app.models.user import User  # noqa: F401 — importé pour qu'Alembic voie le modèle
from app.models.token import Token  # noqa: F401 — importé pour qu'Alembic voie le modèle

# Objet de configuration Alembic (lit alembic.ini)
config = context.config

# Injecte l'URL de la base depuis notre .env (au lieu d'alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configuration du logging Python via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata cible pour l'autogénération des migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()