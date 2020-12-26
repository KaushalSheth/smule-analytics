CREATE OR REPLACE VIEW favorite_partner AS
with
perf_stats as (
    select 	partner_account_id, performers as partner_name,
            count(*) as performance_cnt,
            round((extract(epoch from (now() - min(created_at)))/3600/24)::decimal, 2) as days_since_first_performance,
            sum(
                -- Recent performances should count for more than older performances
                case
                    when days_since_performance < 5 then 16
                    when days_since_performance < 30 then 8
                    when days_since_performance < 60 then 4
                    when days_since_performance < 90 then 2
                    else 1
                end *
                -- Joins should count for more than other performances
                case when owner_handle = 'KaushalSheth1' then 5 else 1 end
            ) as recency_performance_score,
            count(case when created_at > now() - interval '14 days' then 1 else null end) as performance_last_14_days_cnt,
            count(case when owner_handle = 'KaushalSheth1' then 1 else null end) as join_cnt,
            count(case when owner_handle = 'KaushalSheth1' and created_at > now() - interval '14 days' then 1 else null end) as join_last_14_days_cnt
    from 	my_performances
    where 	performers != 'KaushalSheth1'
    and     performers not in (select item_name from exclude_list where list_type = 'PARTNER')
    group by 1, 2
    ),
favorites as (
    select 	partner_name, count(*) as favorite_cnt
    from 	my_favorites
    group by 1
    )
select 	p.partner_account_id, p.partner_name, p.performance_cnt, p.join_cnt, coalesce(f.favorite_cnt,0) as favorite_cnt,
        p.performance_last_14_days_cnt, p.join_last_14_days_cnt,
        least(10.0,1.0*p.performance_cnt/10) +
            least(10.0,1.0*p.join_cnt/2) +
            case
                when f.favorite_cnt is null then 0
                when f.favorite_cnt > 20 then 8
                when f.favorite_cnt > 15 then 7
                when f.favorite_cnt > 10 then 6
                when f.favorite_cnt >= 5 then 5
                else f.favorite_cnt
            end +
            (1.0*p.performance_last_14_days_cnt/2) +
            p.join_last_14_days_cnt as rating,
            p.recency_performance_score + greatest(0,100-p.days_since_first_performance) as recency_score
from 	perf_stats p
        left outer join favorites f on f.partner_name = p.partner_name
;
