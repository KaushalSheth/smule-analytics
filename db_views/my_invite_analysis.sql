create or replace view my_invite_analysis as
with
my_perf as (
    select  fixed_title,
            count(*) as num_all_performances,
            count(case when web_url like '%/ensembles' then 1 else null end) as num_invites,
            coalesce(min(case when web_url like '%/ensembles' then created_at else null end),'2000-01-01'::timestamp) as first_invite_time,
            coalesce(max(case when web_url like '%/ensembles' then created_at else null end),'2000-01-01'::timestamp) as last_invite_time,
            min(created_at) as first_performance_time,
            max(created_at) as last_performance_time,
            count(distinct partner_name) as num_partners,
            string_agg(distinct partner_name,', ') partner_list,
            sum(child_count) AS num_joins
    from    my_performances
    group by 1
    ),
my_perf_metrics as (
    select
            date_part('day',now()-(first_invite_time)) as days_since_first_invite,
            date_part('day',now()-(last_invite_time)) as days_since_last_invite,
            date_part('day',now()-(first_performance_time)) as days_since_first_performance,
            date_part('day',now()-(last_performance_time)) as days_since_last_performance,
            *
    from    my_perf
    ),
my_perf_bucketed as (
    select  case
                when num_all_performances > 50 then '1 >50'
                when num_all_performances > 40 then '2 >40'
                when num_all_performances > 30 then '3 >30'
                when num_all_performances > 20 then '4 >20'
                when num_all_performances > 10 then '5 >10'
                else '6 1-10'
            end popularity_score,
            case
                when days_since_last_invite > 3650 then '0 Never'
                when days_since_last_invite > 365 then '1 >1 year'
                when days_since_last_invite > 90 then '2 >3 months'
                when days_since_last_invite > 60 then '3 >2 months'
                when days_since_last_invite > 30 then '4 >1 month'
                else '5 <1 month'
            end invite_recency_score,
            case
                when days_since_last_performance > 365 then '1 >1 year'
                when days_since_last_performance > 90 then '2 >3 months'
                when days_since_last_performance > 60 then '3 >2 months'
                when days_since_last_performance > 30 then '4 >1 month'
                else '5 <1 month'
            end performance_recency_score,
            case
                when days_since_first_performance > 365 then '1 >1 year'
                when days_since_first_performance > 90 then '2 >3 months'
                when days_since_first_performance > 60 then '3 >2 months'
                when days_since_first_performance > 30 then '4 >1 month'
                else '5 <1 month'
            end first_performance_score,
            *
    from    my_perf_metrics
    ),
my_perf_numerics as (
    select  *,
            substr(popularity_score,1,1)::integer as popularity_score_nbr,
            substr(invite_recency_score,1,1)::integer as invite_recency_score_nbr,
            substr(performance_recency_score,1,1)::integer as performance_recency_score_nbr
    from    my_perf_bucketed
    )
select
        popularity_score,
        invite_recency_score,
        performance_recency_score,
        days_since_first_invite,
        days_since_last_invite,
        days_since_first_performance,
        days_since_last_performance,
        fixed_title,
        num_all_performances,
        num_invites,
        first_invite_time,
        last_invite_time,
        first_performance_time,
        last_performance_time,
        num_partners,
        partner_list,
        popularity_score_nbr,
        invite_recency_score_nbr,
        performance_recency_score_nbr,
        popularity_score_nbr + invite_recency_score_nbr + performance_recency_score_nbr as total_score,
        num_joins,
        first_performance_score
from    my_perf_numerics
;
