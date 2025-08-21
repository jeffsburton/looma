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

def _auto_seed_on_version_apply(**kwargs) -> None:
    """Alembic on_version_apply callback to auto-run seed scripts.

    This runs once per migration step, after the migration's operations
    have been applied but before the transaction is finalized.
    """
    try:
        # Allow opting out via env var
        if os.getenv("ALEMBIC_AUTO_SEED", "1").lower() in {"0", "false", "no"}:
            return

        step = kwargs.get("step")  # alembic.runtime.migration.MigrationInfo
        if step is None:
            return
        # Only run for real upgrade migrations
        if not getattr(step, "is_migration", False) or not getattr(step, "is_upgrade", False):
            return

        up_rev = getattr(step, "up_revision_id", None)
        if not up_rev:
            return

        seeds_dir = Path(__file__).resolve().parent / "seeds"
        seed_filename = f"{up_rev}_seed.py"
        seed_path = seeds_dir / seed_filename
        if not seed_path.exists():
            logger.info("No seed script found for revision %s at %s", up_rev, seed_path)
            return

        mod_name = f"alembic_auto_seed_{up_rev}"
        spec = importlib.util.spec_from_file_location(mod_name, str(seed_path))
        if spec is None or spec.loader is None:
            logger.warning("Could not load seed module for revision %s from %s", up_rev, seed_path)
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Candidate function names in priority order
        candidates = [f"seed_{up_rev}", "upgrade_seed", "seed", "run"]
        func = None
        for name in candidates:
            func = getattr(module, name, None)
            if callable(func):
                break
        if not callable(func):
            logger.warning(
                "Seed module %s does not define any of %s; skipping",
                seed_path,
                candidates,
            )
            return

        logger.info("Running seed function '%s' from %s", getattr(func, "__name__", "<callable>"), seed_path)
        func()
    except Exception as exc:
        # Fail the migration if seeds fail; adjust here if you want best-effort
        logger.error("Error running seeds for revision: %s", exc, exc_info=True)
        raise


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
            on_version_apply=(_auto_seed_on_version_apply,),
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

