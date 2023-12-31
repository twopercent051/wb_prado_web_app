"""empty message

Revision ID: cfce79de4f31
Revises: c6f4bba6f1af
Create Date: 2023-09-04 15:13:18.258365

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfce79de4f31'
down_revision = 'c6f4bba6f1af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('order_id', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'orders', ['order_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'orders', type_='unique')
    op.drop_column('orders', 'order_id')
    # ### end Alembic commands ###
