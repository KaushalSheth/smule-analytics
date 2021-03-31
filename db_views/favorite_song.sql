CREATE OR REPLACE VIEW favorite_song AS
with
perf_day_counts as (
	select a.fixed_title,a.created_at,
		count(case when b.created_at <= a.created_at + interval '30 days' then 1 else null end) as perf_30day_cnt,
		count(case when b.created_at <= a.created_at + interval '10 days' then 1 else null end) as perf_10day_cnt,
		count(case when b.created_at <= a.created_at + interval '5 days' then 1 else null end) as perf_5day_cnt,
		count(case when b.created_at <= a.created_at + interval '1 days' then 1 else null end) as perf_1day_cnt
	from my_performances a
		inner join my_performances b on b.fixed_title = a.fixed_title and b.created_at between a.created_at and a.created_at + interval '30 days'
	group by 1,2
	),
perf_stats as (
	select 	fixed_title, min(created_at) as first_performance_time,
			max(perf_30day_cnt) as perf_30day_cnt,
			max(perf_10day_cnt) as perf_10day_cnt,
			max(perf_5day_cnt) as perf_5day_cnt,
			max(perf_1day_cnt) as perf_1day_cnt,
			count(*) as perf_cnt
	from 	perf_day_counts
	group by 1
	)
select 	ps.fixed_title, ps.first_performance_time, ps.perf_cnt,
		ps.perf_30day_cnt, ps.perf_10day_cnt, ps.perf_5day_cnt, ps.perf_1day_cnt,
		(
			(ps.perf_1day_cnt*300) +
			(ps.perf_5day_cnt*60) +
            (ps.perf_10day_cnt*30) +
            (ps.perf_30day_cnt*10) +
			ps.perf_cnt
		) weighted_cnt
from 	perf_stats ps
;
