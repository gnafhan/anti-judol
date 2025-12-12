"""Add validation_feedback and model_versions tables

Revision ID: a1b2c3d4e5f6
Revises: 59b5aa13fff6
Create Date: 2025-12-11 10:00:00.000000

Requirements: 9.1, 5.3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '59b5aa13fff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create model_versions table first (referenced by validation_feedback)
    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('training_samples', sa.Integer(), nullable=False),
        sa.Column('validation_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall_score', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index('ix_model_versions_is_active', 'model_versions', ['is_active'], unique=False)

    # Create validation_feedback table
    op.create_table(
        'validation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('original_prediction', sa.Boolean(), nullable=False),
        sa.Column('original_confidence', sa.Float(), nullable=False),
        sa.Column('corrected_label', sa.Boolean(), nullable=False),
        sa.Column('is_correction', sa.Boolean(), nullable=False),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('used_in_training', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['scan_result_id'], ['scan_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_validation_feedback_user_id', 'validation_feedback', ['user_id'], unique=False)
    op.create_index('ix_validation_feedback_used_in_training', 'validation_feedback', ['used_in_training'], unique=False)
    op.create_index('ix_validation_feedback_is_correction', 'validation_feedback', ['is_correction'], unique=False)
    op.create_index('ix_validation_feedback_unique', 'validation_feedback', ['scan_result_id', 'user_id'], unique=True)


def downgrade() -> None:
    # Drop validation_feedback table first (has FK to model_versions)
    op.drop_index('ix_validation_feedback_unique', table_name='validation_feedback')
    op.drop_index('ix_validation_feedback_is_correction', table_name='validation_feedback')
    op.drop_index('ix_validation_feedback_used_in_training', table_name='validation_feedback')
    op.drop_index('ix_validation_feedback_user_id', table_name='validation_feedback')
    op.drop_table('validation_feedback')

    # Drop model_versions table
    op.drop_index('ix_model_versions_is_active', table_name='model_versions')
    op.drop_table('model_versions')
