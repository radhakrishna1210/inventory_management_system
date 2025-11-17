"""Add customer table for customer accounts

Revision ID: 9c3d7e2f5c14
Revises: 4428d6a86493
Create Date: 2025-11-17 21:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c3d7e2f5c14'
down_revision = '4428d6a86493'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'customer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )


def downgrade():
    op.drop_table('customer')

