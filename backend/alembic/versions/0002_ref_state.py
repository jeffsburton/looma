"""add ref_state table

Revision ID: 0002
Revises: 0001
Create Date: 2025-08-19 06:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.base import seed

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ref_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ref_state_id'), 'ref_state', ['id'], unique=False)
    op.create_index(op.f('ix_ref_state_code'), 'ref_state', ['code'], unique=True)

    # Seed 50 states (alphabetically) followed by DC and U.S. territories
    seed(
        "ref_state",
        [
            {"name": "Alabama", "code": "AL"},
            {"name": "Alaska", "code": "AK"},
            {"name": "Arizona", "code": "AZ"},
            {"name": "Arkansas", "code": "AR"},
            {"name": "California", "code": "CA"},
            {"name": "Colorado", "code": "CO"},
            {"name": "Connecticut", "code": "CT"},
            {"name": "Delaware", "code": "DE"},
            {"name": "Florida", "code": "FL"},
            {"name": "Georgia", "code": "GA"},
            {"name": "Hawaii", "code": "HI"},
            {"name": "Idaho", "code": "ID"},
            {"name": "Illinois", "code": "IL"},
            {"name": "Indiana", "code": "IN"},
            {"name": "Iowa", "code": "IA"},
            {"name": "Kansas", "code": "KS"},
            {"name": "Kentucky", "code": "KY"},
            {"name": "Louisiana", "code": "LA"},
            {"name": "Maine", "code": "ME"},
            {"name": "Maryland", "code": "MD"},
            {"name": "Massachusetts", "code": "MA"},
            {"name": "Michigan", "code": "MI"},
            {"name": "Minnesota", "code": "MN"},
            {"name": "Mississippi", "code": "MS"},
            {"name": "Missouri", "code": "MO"},
            {"name": "Montana", "code": "MT"},
            {"name": "Nebraska", "code": "NE"},
            {"name": "Nevada", "code": "NV"},
            {"name": "New Hampshire", "code": "NH"},
            {"name": "New Jersey", "code": "NJ"},
            {"name": "New Mexico", "code": "NM"},
            {"name": "New York", "code": "NY"},
            {"name": "North Carolina", "code": "NC"},
            {"name": "North Dakota", "code": "ND"},
            {"name": "Ohio", "code": "OH"},
            {"name": "Oklahoma", "code": "OK"},
            {"name": "Oregon", "code": "OR"},
            {"name": "Pennsylvania", "code": "PA"},
            {"name": "Rhode Island", "code": "RI"},
            {"name": "South Carolina", "code": "SC"},
            {"name": "South Dakota", "code": "SD"},
            {"name": "Tennessee", "code": "TN"},
            {"name": "Texas", "code": "TX"},
            {"name": "Utah", "code": "UT"},
            {"name": "Vermont", "code": "VT"},
            {"name": "Virginia", "code": "VA"},
            {"name": "Washington", "code": "WA"},
            {"name": "West Virginia", "code": "WV"},
            {"name": "Wisconsin", "code": "WI"},
            {"name": "Wyoming", "code": "WY"},
            # Others: DC and U.S. territories
            {"name": "District of Columbia", "code": "DC"},
            {"name": "American Samoa", "code": "AS"},
            {"name": "Guam", "code": "GU"},
            {"name": "Northern Mariana Islands", "code": "MP"},
            {"name": "Puerto Rico", "code": "PR"},
            {"name": "U.S. Virgin Islands", "code": "VI"},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_ref_state_code'), table_name='ref_state')
    op.drop_index(op.f('ix_ref_state_id'), table_name='ref_state')
    op.drop_table('ref_state')
