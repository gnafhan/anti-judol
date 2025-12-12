"""add_is_own_video_to_scans

Revision ID: 59b5aa13fff6
Revises: 7d86b515e984
Create Date: 2025-12-11 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59b5aa13fff6'
down_revision: Union[str, None] = '7d86b515e984'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_own_video column to scans table
    op.add_column('scans', sa.Column('is_own_video', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_own_video column from scans table
    op.drop_column('scans', 'is_own_video')
