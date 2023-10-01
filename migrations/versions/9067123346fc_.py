"""empty message

Revision ID: 9067123346fc
Revises: 3eba1c0f01d6
Create Date: 2023-09-03 20:14:24.024686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9067123346fc'
down_revision = '3eba1c0f01d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('order_id', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('article', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('seller_price', sa.Integer(), nullable=False))
    op.add_column('orders', sa.Column('client_price', sa.Integer(), nullable=False))
    op.add_column('orders', sa.Column('create_dtime', sa.DateTime(), nullable=False))
    op.add_column('orders', sa.Column('seller_status', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('client_status', sa.String(), nullable=False))
    op.add_column('orders', sa.Column('finish_dtime', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'finish_dtime')
    op.drop_column('orders', 'client_status')
    op.drop_column('orders', 'seller_status')
    op.drop_column('orders', 'create_dtime')
    op.drop_column('orders', 'client_price')
    op.drop_column('orders', 'seller_price')
    op.drop_column('orders', 'article')
    op.drop_column('orders', 'order_id')
    # ### end Alembic commands ###
