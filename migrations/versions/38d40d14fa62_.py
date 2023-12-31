"""empty message

Revision ID: 38d40d14fa62
Revises: 57334b893c10
Create Date: 2023-10-18 14:24:26.163187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38d40d14fa62'
down_revision = '57334b893c10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stocks', sa.Column('barcode', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('stocks', 'barcode')
    # ### end Alembic commands ###
