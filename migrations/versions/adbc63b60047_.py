"""empty message

Revision ID: adbc63b60047
Revises: f0be44d66ecb
Create Date: 2020-06-30 21:05:23.774179

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adbc63b60047'
down_revision = 'f0be44d66ecb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('title_mapping',
    sa.Column('smule_title', sa.String(length=100), nullable=False),
    sa.Column('mapped_title', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('smule_title')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('title_mapping')
    # ### end Alembic commands ###
