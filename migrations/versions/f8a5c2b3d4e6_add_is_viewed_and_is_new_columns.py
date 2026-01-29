"""Add is_viewed to posts and is_new to comments

Revision ID: f8a5c2b3d4e6
Revises: e3658856fb82
Create Date: 2026-01-26 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a5c2b3d4e6'
down_revision = ('e3658856fb82', 'dee34f827197')  # Merge both heads
branch_labels = None
depends_on = None


def upgrade():
    # Add is_viewed column to facebook_posts table
    op.add_column('facebook_posts', sa.Column('is_viewed', sa.Boolean(), nullable=True, server_default='0'))
    
    # Add is_new column to facebook_comments table
    op.add_column('facebook_comments', sa.Column('is_new', sa.Boolean(), nullable=True, server_default='1'))


def downgrade():
    # Remove is_new column from facebook_comments table
    op.drop_column('facebook_comments', 'is_new')
    
    # Remove is_viewed column from facebook_posts table
    op.drop_column('facebook_posts', 'is_viewed')
