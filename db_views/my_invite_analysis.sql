drop view my_invite_analysis;
create or replace view my_invite_analysis as
with
title_favorites as (select fixed_title, adj_weighted_cnt as favorite_score_nbr, coalesce(rating_nbr,0) as rating_nbr, singer_type, artist from favorite_song order by fixed_title),
my_perf as (
    select  fixed_title,
            count(*) as num_all_performances,
            count(case when web_url like '%/ensembles' then 1 else null end) as num_invites,
            coalesce(min(case when web_url like '%/ensembles' then created_at else null end),'2000-01-01'::timestamp) as first_invite_time,
            coalesce(max(case when web_url like '%/ensembles' then created_at else null end),'2000-01-01'::timestamp) as last_invite_time,
            min(created_at) as first_performance_time,
            max(created_at) as last_performance_time,
            count(distinct partner_alltime) as num_partners,
            string_agg(distinct partner_alltime,', ') partner_list,
            sum(join_ind) AS num_joins
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
                when num_all_performances > 200 then 'P:0 200+'
                when num_all_performances > 100 then 'P:1 100+'
                when num_all_performances > 50 then 'P:2 50+'
                when num_all_performances > 25 then 'P:3 25+'
                when num_all_performances > 10 then 'P:4 10+'
                when num_all_performances > 5 then 'P:5 5+'
                else 'P:6 1-5'
            end popularity_score,
            case
                when days_since_last_invite > 3650 then 'I:9 Never'
                when days_since_last_invite > 1095 then 'I:1 3+ years'
                when days_since_last_invite > 730 then 'I:2 2+ years'
                when days_since_last_invite > 365 then 'I:3 1+ year'
                when days_since_last_invite > 180 then 'I:4 6+ months'
                when days_since_last_invite > 90 then 'I:5 3+ months'
                else 'I:6 <3 months'
            end invite_recency_score,
            case
                when days_since_last_performance > 1095 then 'R:1 3+ years'
                when days_since_last_performance > 730 then 'R:2 2+ years'
                when days_since_last_performance > 365 then 'R:3 1+ year'
                when days_since_last_performance > 180 then 'R:4 6+ months'
                when days_since_last_performance > 90 then 'R:5 3+ months'
                else 'R:6 <3 months'
            end performance_recency_score,
            case
                when days_since_first_performance > 1095 then 'F:1 3+ years'
                when days_since_first_performance > 730 then 'F:2 2+ years'
                when days_since_first_performance > 365 then 'F:3 1+ year'
                when days_since_first_performance > 180 then 'F:4 6+ months'
                when days_since_first_performance > 90 then 'F:5 3+ months'
                else 'F:6 <3 months'
            end first_performance_score,
            *
    from    my_perf_metrics
    ),
my_perf_numerics as (
    select  pb.*,
            substr(pb.popularity_score,3,1)::integer as popularity_score_nbr,
            substr(pb.invite_recency_score,3,1)::integer as invite_recency_score_nbr,
            substr(pb.performance_recency_score,3,1)::integer as performance_recency_score_nbr,
            tf.favorite_score_nbr, tf.rating_nbr, tf.singer_type, tf.artist
    from    my_perf_bucketed pb
            left outer join title_favorites tf on tf.fixed_title = pb.fixed_title
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
        first_performance_score,
        favorite_score_nbr,
        rating_nbr,
        singer_type,
        artist
from    my_perf_numerics
;
