"""Initial migration - create users, scans, and scan_results tables

Revision ID: 7d86b515e984
Revises: 
Create Date: 2025-12-05 16:06:21.824466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7d86b515e984'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('google_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_id'),
    )
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=False)

    # Create scans table
    op.create_table(
        'scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', sa.String(50), nullable=False),
        sa.Column('video_title', sa.String(500), nullable=True),
        sa.Column('video_thumbnail', sa.String(500), nullable=True),
        sa.Column('channel_name', sa.String(255), nullable=True),
        sa.Column('total_comments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gambling_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clean_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scans_video_id', 'scans', ['video_id'], unique=False)
    op.create_index('ix_scans_status', 'scans', ['status'], unique=False)
    op.create_index('ix_scans_user_id', 'scans', ['user_id'], unique=False)

    # Create scan_results table
    op.create_table(
        'scan_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', sa.String(255), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('author_avatar', sa.String(500), nullable=True),
        sa.Column('is_gambling', sa.Boolean(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scan_results_scan_id', 'scan_results', ['scan_id'], unique=False)
    op.create_index('ix_scan_results_is_gambling', 'scan_results', ['is_gambling'], unique=False)


def downgrade() -> None:
    # Drop scan_results table
    op.drop_index('ix_scan_results_is_gambling', table_name='scan_results')
    op.drop_index('ix_scan_results_scan_id', table_name='scan_results')
    op.drop_table('scan_results')

    # Drop scans table
    op.drop_index('ix_scans_user_id', table_name='scans')
    op.drop_index('ix_scans_status', table_name='scans')
    op.drop_index('ix_scans_video_id', table_name='scans')
    op.drop_table('scans')

    # Drop users table
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_table('users')
