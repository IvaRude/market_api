"""initial

Revision ID: 35a34feabb5e
Revises: 
Create Date: 2022-06-20 11:18:32.708840

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '35a34feabb5e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('items',
    sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('total_price', sa.Integer(), nullable=True),
    sa.Column('amount_of_offers', sa.Integer(), nullable=True),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('timezone', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['items.item_id'], ),
    sa.PrimaryKeyConstraint('item_id')
    )
    op.create_index(op.f('ix_items_date'), 'items', ['date'], unique=False)
    op.create_table('history',
    sa.Column('history_id', sa.Integer(), nullable=False),
    sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('total_price', sa.Integer(), nullable=True),
    sa.Column('amount_of_offers', sa.Integer(), nullable=True),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('timezone', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['item_id'], ['items.item_id'], ),
    sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index(op.f('ix_history_date'), 'history', ['date'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_history_date'), table_name='history')
    op.drop_table('history')
    op.drop_index(op.f('ix_items_date'), table_name='items')
    op.drop_table('items')
    # ### end Alembic commands ###
