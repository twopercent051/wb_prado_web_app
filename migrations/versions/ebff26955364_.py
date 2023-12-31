"""empty message

Revision ID: ebff26955364
Revises: c9898a27b570
Create Date: 2023-09-30 18:46:19.657335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebff26955364'
down_revision = 'c9898a27b570'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('sku', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('products', 'sku')
    # ### end Alembic commands ###
