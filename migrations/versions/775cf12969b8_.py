"""empty message

Revision ID: 775cf12969b8
Revises: adbc63b60047
Create Date: 2020-07-01 20:02:20.569173

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '775cf12969b8'
down_revision = 'adbc63b60047'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #op.drop_table('bkp20200630_performance')
    op.add_column('performance', sa.Column('short_ind', sa.String(length=1), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('performance', 'short_ind')
    op.create_table('bkp20200630_performance',
    sa.Column('key', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('type', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('ensemble_type', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('child_count', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('app_uid', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('arr_key', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('orig_track_city', sa.VARCHAR(length=40), autoincrement=False, nullable=True),
    sa.Column('orig_track_country', sa.VARCHAR(length=40), autoincrement=False, nullable=True),
    sa.Column('media_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('video_media_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('video_media_mp4_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('web_url', sa.VARCHAR(length=300), autoincrement=False, nullable=True),
    sa.Column('total_performers', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_listens', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_loves', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_comments', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_commenters', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('performed_by', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('performed_by_url', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('owner_account_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('owner_lat', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('owner_lon', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('filename', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('owner_handle', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('owner_pic_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('artist', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('cover_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=False, nullable=True),
    sa.Column('expire_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('fixed_title', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('perf_status', sa.VARCHAR(length=1), autoincrement=False, nullable=True),
    sa.Column('performers', sa.VARCHAR(length=100), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###
