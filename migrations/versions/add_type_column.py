
"""add type column

Revision ID: add_type_column
Revises: 
Create Date: 2023-12-19
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('exchanges', sa.Column('type', sa.String(50)))
    op.execute("UPDATE exchanges SET type = 'forex' WHERE exchange_type = 'oanda'")
    op.execute("UPDATE exchanges SET type = 'crypto' WHERE exchange_type != 'oanda'")

def downgrade():
    op.drop_column('exchanges', 'type')
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('exchanges', sa.Column('type', sa.String(50)))
    
def downgrade():
    op.drop_column('exchanges', 'type')
