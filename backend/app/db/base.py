from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from alembic import op
import sqlalchemy as sa

Base = declarative_base()

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

def seed(table_name: str, row: dict) -> int:
    """Insert a row into the given table using the current Alembic bind and return the new id.

    Args:
        table_name: Name of the target table.
        row: Mapping of column -> value to insert.

    Returns:
        The primary key value of the inserted row (assumes a single-column PK).
    """
    bind = op.get_bind()

    # Reflect the table structure against the current migration connection
    metadata = sa.MetaData()
    table = sa.Table(table_name, metadata, autoload_with=bind)

    # Identify primary key column (assumes single-column PK). Fallback to 'id'.
    pk_cols = list(table.primary_key.columns)
    pk_col = None
    if len(pk_cols) == 1:
        pk_col = pk_cols[0]
    elif 'id' in table.c:
        pk_col = table.c['id']
    elif pk_cols:
        pk_col = pk_cols[0]

    insert_stmt = sa.insert(table).values(**row)

    # If dialect supports RETURNING and we know the PK column, use it.
    if pk_col is not None and bind.dialect.name in {"postgresql", "postgres"}:
        insert_stmt = insert_stmt.returning(pk_col)
        result = bind.execute(insert_stmt)
        inserted_id = result.scalar_one()
        return int(inserted_id)

    # Fallback execute and try to obtain PK from result metadata
    result = bind.execute(insert_stmt)

    # SQLAlchemy 1.4/2.0 provides inserted_primary_key when available
    inserted_pk = getattr(result, 'inserted_primary_key', None)
    if inserted_pk:
        return int(inserted_pk[0])

    # Some DBAPIs expose lastrowid
    lastrowid = getattr(result, 'lastrowid', None)
    if lastrowid is not None:
        return int(lastrowid)

    raise RuntimeError("Could not determine inserted id for table '%s'" % table_name)