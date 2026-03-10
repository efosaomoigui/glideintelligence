"""Add AI analysis enhancements

Revision ID: 2026_02_15_0350
Revises: bd516b2a51d6
Create Date: 2026-02-15 03:50:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2026_02_15_0350'
down_revision = 'bd516b2a51d6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create category_configs table
    op.create_table('category_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('dimension_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('impact_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category')
    )
    op.create_index(op.f('ix_category_configs_category'), 'category_configs', ['category'], unique=False)
    
    # 2. Drop old topic_sentiment_breakdown table
    op.drop_table('topic_sentiment_breakdown')
    
    # 3. Create new dimension-based topic_sentiment_breakdown table
    op.create_table('topic_sentiment_breakdown',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('dimension_type', sa.String(length=50), nullable=False),
        sa.Column('dimension_value', sa.String(length=100), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_sentiment_breakdown_topic_id'), 'topic_sentiment_breakdown', ['topic_id'], unique=False)
    op.create_index(op.f('ix_topic_sentiment_breakdown_dimension_type'), 'topic_sentiment_breakdown', ['dimension_type'], unique=False)
    
    # 4. Create source_perspectives table
    op.create_table('source_perspectives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('frame_label', sa.String(length=100), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=False),
        sa.Column('sentiment_percentage', sa.String(length=10), nullable=False),
        sa.Column('key_narrative', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_perspectives_topic_id'), 'source_perspectives', ['topic_id'], unique=False)
    
    # 5. Create intelligence_cards table
    op.create_table('intelligence_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('icon', sa.String(length=10), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=False),
        sa.Column('trend_percentage', sa.String(length=10), nullable=False),
        sa.Column('is_positive', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('topic_id')
    )
    op.create_index(op.f('ix_intelligence_cards_topic_id'), 'intelligence_cards', ['topic_id'], unique=False)
    op.create_index(op.f('ix_intelligence_cards_display_order'), 'intelligence_cards', ['display_order'], unique=False)


def downgrade():
    # Drop new tables
    op.drop_index(op.f('ix_intelligence_cards_display_order'), table_name='intelligence_cards')
    op.drop_index(op.f('ix_intelligence_cards_topic_id'), table_name='intelligence_cards')
    op.drop_table('intelligence_cards')
    
    op.drop_index(op.f('ix_source_perspectives_topic_id'), table_name='source_perspectives')
    op.drop_table('source_perspectives')
    
    op.drop_index(op.f('ix_topic_sentiment_breakdown_dimension_type'), table_name='topic_sentiment_breakdown')
    op.drop_index(op.f('ix_topic_sentiment_breakdown_topic_id'), table_name='topic_sentiment_breakdown')
    op.drop_table('topic_sentiment_breakdown')
    
    op.drop_index(op.f('ix_category_configs_category'), table_name='category_configs')
    op.drop_table('category_configs')
    
    # Recreate old topic_sentiment_breakdown table
    op.create_table('topic_sentiment_breakdown',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('positive', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('neutral', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('negative', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('topic_id')
    )
    op.create_index(op.f('ix_topic_sentiment_breakdown_topic_id'), 'topic_sentiment_breakdown', ['topic_id'], unique=True)
