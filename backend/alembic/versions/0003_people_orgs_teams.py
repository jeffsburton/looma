"""add person, organization, qualification, team, and associations

Revision ID: 0003
Revises: 0002
Create Date: 2025-08-19 07:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.base import seed, get_record_by_code

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organization first (no hard requirement, but referenced by person)
    op.create_table(
        'organization',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('main_contact_id', sa.Integer(), nullable=True),
        sa.Column('ref_state_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ref_state_id'], ['ref_state.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_id'), 'organization', ['id'], unique=False)

    # person
    op.create_table(
        'person',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=120), nullable=False),
        sa.Column('last_name', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_person_id'), 'person', ['id'], unique=False)

    # Now that person exists, add FK from organization.main_contact_id -> person.id
    op.create_foreign_key(
        'fk_organization_main_contact_id_person',
        source_table='organization',
        referent_table='person',
        local_cols=['main_contact_id'],
        remote_cols=['id'],
    )

    # qualification
    op.create_table(
        'qualification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qualification_id'), 'qualification', ['id'], unique=False)
    op.create_index(op.f('ix_qualification_code'), 'qualification', ['code'], unique=False)

    # person_qualification
    op.create_table(
        'person_qualification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('qualification_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['qualification_id'], ['qualification.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_person_qualification_id'), 'person_qualification', ['id'], unique=False)

    # team
    op.create_table(
        'team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('inactive', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_id'), 'team', ['id'], unique=False)
    op.create_index(op.f('ix_team_name'), 'team', ['name'], unique=False)

    # team_role
    op.create_table(
        'team_role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_role_id'), 'team_role', ['id'], unique=False)
    op.create_index(op.f('ix_team_role_code'), 'team_role', ['code'], unique=True)

    # person_team
    op.create_table(
        'person_team',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('team_role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_role_id'], ['team_role.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_person_team_id'), 'person_team', ['id'], unique=False)

    # Seed team_role entries
    seed(
        'team_role',
        [
            {"name": "Leader", "code": "LEAD"},
            {"name": "Assistant Leader", "code": "ASST"},
            {"name": "Case Advocate", "code": "CADV"},
            {"name": "Intel Analyst", "code": "INTEL"},
            {"name": "Operations", "code": "OPS"},
            {"name": "Ministry", "code": "MIN"},
        ]
    )

    # Seed organization entry (name, ref_state_id=9)
    seed('organization', {"name": "Called2Rescue", "ref_state_id": 9})

    # see qualifications
    seed(
        'qualification',
        [
            {"name": "Fundamentals", "code": "FUND"},
            {"name": "Leadership", "code": "LEAD"},
            {"name": "Case Advocay", "code": "CADV"},
            {"name": "Intel Analyst", "code": "INTEL"},
            {"name": "Operations", "code": "OPS"},
            {"name": "FBI Background Check", "code": "BACK"},
            {"name": "Concealed Carry Permit", "code": "CCP"},
            {"name": "Stop The Bleed", "code": "STB"},
            {"name": "FEMA IS-100", "code": "F100"},
            {"name": "FEMA IS-200", "code": "F200"}
        ]
    )

    perm_id: int = seed("permission", {"name": "Edit Organizations", "code": "ADMIN.ORGS", "description": "Edit the list of organizations in admin."})
    role_id: int = get_record_by_code("role", "ADMIN")
    seed("role_permission", {"role_id": role_id, "permission_id": perm_id})


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index(op.f('ix_person_team_id'), table_name='person_team')
    op.drop_table('person_team')

    op.drop_index(op.f('ix_team_role_code'), table_name='team_role')
    op.drop_index(op.f('ix_team_role_id'), table_name='team_role')
    op.drop_table('team_role')

    op.drop_index(op.f('ix_team_name'), table_name='team')
    op.drop_index(op.f('ix_team_id'), table_name='team')
    op.drop_table('team')

    op.drop_index(op.f('ix_person_qualification_id'), table_name='person_qualification')
    op.drop_table('person_qualification')

    op.drop_index(op.f('ix_qualification_code'), table_name='qualification')
    op.drop_index(op.f('ix_qualification_id'), table_name='qualification')
    op.drop_table('qualification')

    # drop FK from organization to person before dropping person
    op.drop_constraint('fk_organization_main_contact_id_person', 'organization', type_='foreignkey')
    op.drop_index(op.f('ix_person_id'), table_name='person')
    op.drop_table('person')

    op.drop_index(op.f('ix_organization_id'), table_name='organization')
    op.drop_table('organization')
