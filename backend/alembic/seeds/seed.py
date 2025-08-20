

from alembic import op
import sqlalchemy as sa

def seed(table_name: str, rows) -> int | list[int]:
    """Insert one or many rows into the given table using the current Alembic bind.

    Args:
        table_name: Name of the target table.
        rows: Either a single mapping (dict) of column -> value to insert,
              or a list/tuple of such mappings for bulk insert.

    Returns:
        - If a single row (dict) is provided: the primary key value (int) of the inserted row
          (assumes a single-column PK).
        - If a list/tuple of rows is provided:
            * On PostgreSQL (supports RETURNING): list[int] of inserted primary keys.
            * On other dialects: an empty list (IDs not available for bulk insert without RETURNING).

    Notes:
        - If an empty list is provided, returns an empty list immediately.
        - Primary key detection assumes a single-column PK; falls back to 'id' if present.
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

    is_sequence = isinstance(rows, (list, tuple))

    # Handle bulk insert
    if is_sequence:
        if len(rows) == 0:
            return []
        insert_stmt = sa.insert(table).values(list(rows))
        if pk_col is not None and bind.dialect.name in {"postgresql", "postgres"}:
            insert_stmt = insert_stmt.returning(pk_col)
            result = bind.execute(insert_stmt)
            # When returning a single column, scalars() is available
            inserted_ids = list(result.scalars())
            return [int(x) for x in inserted_ids]
        else:
            # Execute without RETURNING; cannot reliably fetch PKs for bulk insert on many dialects
            bind.execute(insert_stmt)
            return []

    # Single-row insert (backward compatible)
    row = rows
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

def get_record_by_code(table_name: str, code: str) -> int:
    """Fetch the primary key (id) for the row in `table_name` with the given `code`.

    Uses the current Alembic migration connection (op.get_bind()) and table
    reflection, similar to `seed`.

    Args:
        table_name: Name of the table to query.
        code: The value to match against the table's `code` column.

    Returns:
        int: The primary key value (id or single-column primary key) of the
        matching row.

    Raises:
        KeyError: If the table has no `code` column.
        LookupError: If no row with the given code is found.
        RuntimeError: If multiple rows are found for the given code, or if a
            unique primary key column cannot be determined.
    """
    bind = op.get_bind()

    # Reflect table structure on the current migration connection
    metadata = sa.MetaData()
    table = sa.Table(table_name, metadata, autoload_with=bind)

    # Ensure there is a `code` column
    if 'code' not in table.c:
        raise KeyError(f"Table '{table_name}' does not have a 'code' column")

    # Determine which column to return as the identifier
    if 'id' in table.c:
        id_col = table.c['id']
    else:
        pk_cols = list(table.primary_key.columns)
        if len(pk_cols) != 1:
            raise RuntimeError(
                f"Table '{table_name}' must have a single-column primary key or an 'id' column"
            )
        id_col = pk_cols[0]

    # Build and execute select query
    stmt = sa.select(id_col).where(table.c['code'] == code)
    result = bind.execute(stmt)
    ids = list(result.scalars())

    if len(ids) == 0:
        raise LookupError(f"No record found in '{table_name}' with code='{code}'")
    if len(ids) > 1:
        raise RuntimeError(f"Multiple records found in '{table_name}' with code='{code}'")

    return int(ids[0])