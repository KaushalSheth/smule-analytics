drop view favorite_partner;
CREATE OR REPLACE VIEW favorite_partner AS
with
sf as (select row_number() over(order by updated_at) as rank_nbr, * from singer_following where is_following),
perf as (
    select  p.*, pf.created_at as rated_datetime,
            greatest(1,30-p.days_since_performance) as performance_weight_nbr,
            case when l.item_name is not null then 1 else 0 end always_include_ind
    from    my_performances p
    left outer join smule_list l on l.list_type = 'INCLUDE_PARTNER' and l.item_name ilike p.performers
    left outer join performance_favorite pf on pf.performance_key = p.key
            -- Eclude my performances
    where   performers != 'KaushalSheth1'
            -- Exclude performers in the exclude list
    and     performers not in (select item_name from smule_list where list_type = 'EXCLUDE_PARTNER')
),
perf_stats as (
    select 	partner_account_id, performers as partner_name, always_include_ind,
            count(*) as performance_cnt,
            sum(join_ind) as join_cnt,
            sum(favorite_ind) as favorite_cnt,
            -- For recent performances, don't count performances in the last 12 hours
            sum(case when days_since_performance between 0.5 and 5 then 1 else 0 end) as recent_perf_cnt,
            sum(case when days_since_performance between 0 and 5 then 1 else 0 end) as performance_last_5_days_cnt,
            sum(case when days_since_performance between 0 and 14 then 1 else 0 end) as performance_last_14_days_cnt,
            sum(case when days_since_performance between 0 and 14 then join_ind else 0 end) as join_last_14_days_cnt,
            sum(case when days_since_performance between 0 and 30 then join_ind else 0 end) as join_last_30_days_cnt,
            case when always_include_ind > 0 then 100000 else 0 end +
                sum(performance_weight_nbr*(case favorite_ind when 1 then 20 else 1 end)*(case join_ind when 1 then 10 else 1 end)) as recency_score,
            max(case when join_ind = 0 then created_at else '2000-01-01'::timestamp end) as last_performance_time,
            min(created_at) as first_performance_time,
            min(case when join_ind = 1 then created_at else null end) as first_join_time,
            max(case when join_ind = 1 then created_at else null end) as last_join_time,
            count(case when rated_datetime > '2021-11-20'::timestamp then 1 else null end) as rated_song_cnt,   -- We started rating songs on 11/20/2021
            round(coalesce(avg(rating_nbr),0.0),2) avg_rating_nbr,
            substring(string_agg(coalesce(rating_nbr::varchar,'-'),'' order by created_at desc),1,10) as last10_rating_str
    from 	perf
    group by 1, 2, 3
)
select 	p.partner_account_id, p.partner_name, p.performance_cnt, p.join_cnt, p.favorite_cnt, p.recent_perf_cnt,
        p.performance_last_14_days_cnt, p.join_last_14_days_cnt, p.join_last_30_days_cnt, p.always_include_ind,
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
        p.last_performance_time,
        p.first_performance_time,
        s.pic_url as display_pic_url,
        coalesce(sf.is_following,false) as is_following,
        coalesce(extract(day from p.first_join_time - p.first_performance_time),-1) days_till_first_join,
        p.first_join_time, p.last_join_time, p.avg_rating_nbr,
        round(case
            when p.performance_cnt <= 5 then p.avg_rating_nbr - 1 -- Not enough performances to get accurate rating, so subtract 1
            when p.rated_song_cnt < (p.performance_cnt/3.0) then p.avg_rating_nbr - greatest((0.75 - p.favorite_cnt/(p.performance_cnt*1.0)),0)
            else p.avg_rating_nbr
        end, 2) as adj_avg_rating_nbr,
        length(last10_rating_str) - length(replace(last10_rating_str,'5','')) as last10_five_cnt,
        length(replace(last10_rating_str,'-','')) as last10_rating_cnt,
        p.rated_song_cnt, p.last10_rating_str, p.performance_last_5_days_cnt,
        sf.rank_nbr
from 	perf_stats p
        left outer join singer s on s.account_id = p.partner_account_id
        left outer join sf on sf.account_id = p.partner_account_id
-- Include all users I'm following with whom I don't have any performances yet
UNION ALL
select  account_id as partner_account_id, handle as partner_name,
        0, 0, 0, 0, 0, 0, 0, 1, 99999, 99999, '1900-01-01'::timestamp, '1900-01-01'::timestamp,
        pic_url, is_following, -1, null, null, 0.0, 0.0, 0, 0, 0, '', 0, rank_nbr
from    sf
where   is_following and is_vip
and     account_id not in (select owner_account_id from my_performances)
;
