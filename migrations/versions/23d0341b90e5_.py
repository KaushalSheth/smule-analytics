"""empty message

Revision ID: 23d0341b90e5
Revises: 4dc27bafe7b5
Create Date: 2020-04-05 13:14:26.024763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23d0341b90e5'
down_revision = '4dc27bafe7b5'
branch_labels = None
depends_on = None


def upgrade():
    # Added by ksheth:
    op.alter_column(table_name='performance',column_name='owner_account_id',type_=sa.BigInteger())
    op.alter_column(table_name='singer',column_name='account_id',type_=sa.BigInteger())
    op.alter_column(table_name='performance_singer',column_name='singer_account_id',type_=sa.BigInteger())

def downgrade():
    # Added by ksheth:
    op.alter_column(table_name='performance',column_name='owner_account_id',type_=sa.Integer())
    op.alter_column(table_name='singer',column_name='account_id',type_=sa.Integer())
    op.alter_column(table_name='performance_singer',column_name='singer_account_id',type_=sa.Integer())
