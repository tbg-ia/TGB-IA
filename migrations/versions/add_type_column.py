
"""add type column

Revision ID: add_type_column
Create Date: 2024-12-19
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add type column if it doesn't exist
    op.add_column('exchanges', sa.Column('type', sa.String(50)))
    
    # Set default value for existing rows
    op.execute("UPDATE exchanges SET type = 'base' WHERE type IS NULL")
    
    # Make column not nullable after setting defaults
    op.alter_column('exchanges', 'type',
                    existing_type=sa.String(50),
                    nullable=False)

def downgrade():
    op.drop_column('exchanges', 'type')
