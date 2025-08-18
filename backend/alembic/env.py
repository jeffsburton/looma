# python
from __future__ import annotations

import importlib
import logging
import os
import pkgutil
import sys
from pathlib import Path
from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure project root is on sys.path (…/ -> contains app/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("alembic.env")

# Import the Base your models inherit from, then set target_metadata
try:
    from app.db import Base  # preferred: app/db/__init__.py re-exports Base
except ModuleNotFoundError:
    from app.db import Base       # fallback if Base is in app/db/__init__.py

target_metadata = Base.metadata

# Packages that may contain models
PACKAGES_TO_SCAN = ["app.models", "app.db.models"]

def _import_models() -> None:
    """Import all model modules so they register on Base.metadata."""
    imported = []
    for pkg_name in PACKAGES_TO_SCAN:
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue

        # If it's a package, walk it; if it's a module, the import above suffices.
        if getattr(pkg, "__path__", None):
            for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
                if ispkg:
                    continue
                try:
                    importlib.import_module(modname)
                    imported.append(modname)
                except Exception as exc:
                    logger.debug("Skipping %s due to: %s", modname, exc)

    tables = ", ".join(sorted(Base.metadata.tables.keys())) or "(none)"
    logger.info("Imported modules: %s", imported or "(none)")
    logger.info("Discovered tables on Base.metadata: %s", tables)

def _get_database_url() -> str:
    # Prefer env var; fallback to alembic.ini sqlalchemy.url if present
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    cfg_url = context.config.get_main_option("sqlalchemy.url")
    if cfg_url:
        return cfg_url
    raise RuntimeError("No database URL found. Set DATABASE_URL or sqlalchemy.url in alembic.ini")

def run_migrations_offline() -> None:
    _import_models()  # ensure models are loaded before autogenerate
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    _import_models()  # ensure models are loaded before autogenerate
    configuration = context.config.get_section(context.config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

