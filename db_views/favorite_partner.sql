CREATE OR REPLACE VIEW favorite_partner AS
with
perf as (
    select  p.*,
            greatest(1,100-p.days_since_performance) as performance_weight_nbr,
            case when f.performance_key is not null then 1 else 0 end favorite_ind,
            case when p.owner_handle = 'KaushalSheth1' then 1 else 0 end join_ind
    from    my_performances p
            left outer join performance_favorite f on f.performance_key = p.key
            -- Eclude my performances
    where   performers != 'KaushalSheth1'
            -- Exclude performers in the exclude list
    and     performers not in (select item_name from exclude_list where list_type = 'PARTNER')
),
perf_stats as (
    select 	partner_account_id, performers as partner_name,
            count(*) as performance_cnt,
            sum(join_ind) as join_cnt,
            sum(favorite_ind) as favorite_cnt,
            sum(case when days_since_performance <= 14 then 1 else 0 end) as performance_last_14_days_cnt,
            sum(case when days_since_performance <= 14 then join_ind else 0 end) as join_last_14_days_cnt,
            sum(performance_weight_nbr*(case favorite_ind when 1 then 20 else 1 end)*(case join_ind when 1 then 10 else 1 end)) as recency_score
    from 	perf
    group by 1, 2
)
select 	p.partner_account_id, p.partner_name, p.performance_cnt, p.join_cnt, p.favorite_cnt,
        p.performance_last_14_days_cnt, p.join_last_14_days_cnt,
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
            p.recency_score
from 	perf_stats p
;
