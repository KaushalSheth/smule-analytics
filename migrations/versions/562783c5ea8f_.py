"""empty message

Revision ID: 562783c5ea8f
Revises: f6924a956897
Create Date: 2019-06-06 04:20:32.265498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '562783c5ea8f'
down_revision = 'f6924a956897'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('performance', sa.Column('artist', sa.String(length=200), nullable=True))
    op.add_column('performance', sa.Column('cover_url', sa.String(length=200), nullable=True))
    op.add_column('performance', sa.Column('title', sa.String(length=200), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('performance', 'title')
    op.drop_column('performance', 'cover_url')
    op.drop_column('performance', 'artist')
    # ### end Alembic commands ###