"""empty message

Revision ID: 654948a05e7c
Revises: a432f4f9f9fb
Create Date: 2022-11-27 21:07:34.085476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '654948a05e7c'
down_revision = 'a432f4f9f9fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('title_metadata',
    sa.Column('fixed_title', sa.String(length=100), nullable=False),
    sa.Column('meta_title', sa.String(length=100), nullable=False),
    sa.Column('artist', sa.String(length=200), nullable=True),
    sa.Column('duration', sa.String(length=10), nullable=True),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('fixed_title')
    )

    with op.batch_alter_table('performance_singer', schema=None) as batch_op:
        batch_op.create_index('i_perfsinger_singer', ['singer_account_id'], unique=False)

    with op.batch_alter_table('performance_favorite', schema=None) as batch_op:
        batch_op.create_index('i_perffav_perfkey', ['performance_key'], unique=False)

    with op.batch_alter_table('performance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_key', sa.VARCHAR(length=30), autoincrement=False, nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('title_metadata')
    # ### end Alembic commands ###