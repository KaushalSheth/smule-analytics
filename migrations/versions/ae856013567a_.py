"""empty message

Revision ID: ae856013567a
Revises: 775cf12969b8
Create Date: 2020-08-31 15:42:48.404644

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ae856013567a'
down_revision = '775cf12969b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('smule_list',
    sa.Column('list_type', sa.String(length=100), nullable=False),
    sa.Column('fixed_title', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('list_type', 'fixed_title')
    )
    #op.drop_table('bkp20200630_performance')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
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
    op.drop_table('smule_list')
    # ### end Alembic commands ###
