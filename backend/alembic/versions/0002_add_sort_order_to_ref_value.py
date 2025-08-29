"""
Add sort_order column and index to ref_value

Revision ID: 0002_add_sort_order_to_ref_value
Revises: 0001_init
Create Date: 2025-08-29
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_sort_order_to_ref_value'
down_revision = '0001_init'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add column if it does not exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('ref_value')]
    if 'sort_order' not in columns:
        op.add_column('ref_value', sa.Column('sort_order', sa.Integer(), nullable=True))
    # Create index if it does not exist
    existing_indexes = [ix['name'] for ix in inspector.get_indexes('ref_value')]
    index_name = 'ix_ref_value_sort_order'
    if index_name not in existing_indexes:
        op.create_index(index_name, 'ref_value', ['sort_order'], unique=False)


def downgrade() -> None:
    # Drop index if exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [ix['name'] for ix in inspector.get_indexes('ref_value')]
    index_name = 'ix_ref_value_sort_order'
    if index_name in existing_indexes:
        op.drop_index(index_name, table_name='ref_value')
    # Drop column if exists
    columns = [c['name'] for c in inspector.get_columns('ref_value')]
    if 'sort_order' in columns:
        op.drop_column('ref_value', 'sort_order')
