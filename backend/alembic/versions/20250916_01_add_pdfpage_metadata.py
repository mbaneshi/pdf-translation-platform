"""add metadata column to pdf_pages

Revision ID: 20250916_01
Revises: 
Create Date: 2025-09-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250916_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pdf_pages', sa.Column('metadata', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('pdf_pages', 'metadata')

