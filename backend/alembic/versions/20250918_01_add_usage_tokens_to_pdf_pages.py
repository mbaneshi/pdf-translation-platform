"""add tokens_in and tokens_out to pdf_pages

Revision ID: 20250918_01
Revises: 20250916_01
Create Date: 2025-09-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250918_01'
down_revision = '20250916_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pdf_pages', sa.Column('tokens_in', sa.Integer(), nullable=True))
    op.add_column('pdf_pages', sa.Column('tokens_out', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('pdf_pages', 'tokens_out')
    op.drop_column('pdf_pages', 'tokens_in')

