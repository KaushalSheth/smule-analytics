"""empty message

Revision ID: 23d0341b90e5_manual
Revises: 23d0341b90e5
Create Date: 2020-04-05 13:41:26.024763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23d0341b90e5_manual'
down_revision = '23d0341b90e5'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(table_name='performance',column_name='web_url',type_=sa.String(length=300))
    sql = """
create or replace view my_performances as
with performances as (
    select  *
    from    performance p
    where   1 = 1
    AND     p.key in (
                select  ps.performance_key
                from    performance_singer ps
                        inner join singer s on s.account_id = ps.singer_account_id
                where   s.performed_by = 'KaushalSheth1'
                )
),
partners as (
    select  owner_handle,
            lpad(cast(count(*) as varchar),3,'0') || '-' || owner_handle as partner_name
    FROM    performances
    group by 1
)
select  p.*, ptr.partner_name,
        trim(replace(substr(filename,1,position('-' in filename)-1),'[Short]', '')) as fixed_title
from    performances p
        inner join partners ptr on ptr.owner_handle = p.owner_handle
"""
    op.execute(sql)

    sql = """
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql'
"""
    op.execute(sql)

    sql = """
DROP TRIGGER update_performance_modtime ON performance
"""
    op.execute(sql)

    sql = """
CREATE TRIGGER update_performance_modtime BEFORE UPDATE ON performance FOR EACH ROW EXECUTE PROCEDURE  update_modified_column()
"""
    op.execute(sql)

def downgrade():
    op.alter_column(table_name='performance',column_name='web_url',type_=sa.String(length=200))
