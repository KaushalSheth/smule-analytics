CREATE OR REPLACE VIEW favorite_partner AS
with
perf as (
    select  p.*,
            greatest(1,30-p.days_since_performance) as performance_weight_nbr,
            case when f.performance_key is not null then 1 else 0 end favorite_ind,
            case when l.item_name is not null then 1 else 0 end always_include_ind
    from    my_performances p
    left outer join performance_favorite f on f.performance_key = p.key
    left outer join exclude_list l on l.list_type = 'INCLUDE_PARTNER' and l.item_name ilike p.performers
            -- Eclude my performances
    where   performers != 'KaushalSheth1'
            -- Exclude performers in the exclude list
    and     performers not in (select item_name from exclude_list where list_type = 'EXCLUDE_PARTNER')
),
perf_stats as (
    select 	partner_account_id, performers as partner_name, always_include_ind,
            count(*) as performance_cnt,
            sum(join_ind) as join_cnt,
            sum(favorite_ind) as favorite_cnt,
            sum(case when days_since_performance <= 14 then 1 else 0 end) as performance_last_14_days_cnt,
            sum(case when days_since_performance <= 14 then join_ind else 0 end) as join_last_14_days_cnt,
            case when always_include_ind > 0 then 100000 else 0 end +
                sum(performance_weight_nbr*(case favorite_ind when 1 then 20 else 1 end)*(case join_ind when 1 then 10 else 1 end)) as recency_score,
            max(case when join_ind = 0 then created_at else '2000-01-01'::timestamp end) as last_performance_time,
            min(created_at) as first_performance_time
    from 	perf
    group by 1, 2, 3
)
select 	p.partner_account_id, p.partner_name, p.performance_cnt, p.join_cnt, p.favorite_cnt,
        p.performance_last_14_days_cnt, p.join_last_14_days_cnt, p.always_include_ind,
        least(10.0,1.0*p.performance_cnt/10) +
            least(10.0,1.0*p.join_cnt/2) +
            case
                when p.favorite_cnt is null then 0
                when p.favorite_cnt > 20 then 8
                when p.favorite_cnt > 15 then 7
                when p.favorite_cnt > 10 then 6
                when p.favorite_cnt >= 5 then 5
                else p.favorite_cnt
            end +
            (1.0*p.performance_last_14_days_cnt/2) +
            p.join_last_14_days_cnt as rating,
            p.recency_score,
            last_performance_time,
            first_performance_time
from 	perf_stats p
;
