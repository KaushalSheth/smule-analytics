"""empty message

Revision ID: 326d72b473f8
Revises: cc35f8a2e6ca
Create Date: 2021-11-23 14:40:55.926443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '326d72b473f8'
down_revision = 'cc35f8a2e6ca'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('geo_cache',
    sa.Column('lat', sa.String(length=10), nullable=False),
    sa.Column('lon', sa.String(length=10), nullable=False),
    sa.Column('city', sa.String(length=40), nullable=True),
    sa.Column('country', sa.String(length=40), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('lat', 'lon')
    )
    op.create_index('i_perfsinger_singer', 'performance_singer', ['singer_account_id'], unique=False)
    op.create_index('i_perffav_perfkey', 'performance_favorite', ['performance_key'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('i_perffav_perfkey', table_name='performance_favorite')
    op.drop_index('i_perfsinger_singer', table_name='performance_singer')
    op.drop_table('geo_cache')
    # ### end Alembic commands ###
