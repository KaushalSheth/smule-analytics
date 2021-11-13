drop view favorite_song;
CREATE OR REPLACE VIEW favorite_song AS
with
perf_day_counts as (
	select a.fixed_title,a.created_at,
		-- Older counts are worth less than recent counts, so reduce older counts accordingly
		-- 0-180: full value, 181-365: 3/4, 366-730: 1/2, 366+: 1/4
		case
			when date_part('day', now() - a.created_at) <= 180 then 1.0
			when date_part('day', now() - a.created_at) <= 365 then 0.75
			when date_part('day', now() - a.created_at) <= 730 then 0.5
			else 0.25
		end adjust_rate,
		count(case when b.created_at <= a.created_at + interval '30 days' then 1 else null end) as perf_30day_cnt,
		count(case when b.created_at <= a.created_at + interval '10 days' then 1 else null end) as perf_10day_cnt,
		count(case when b.created_at <= a.created_at + interval '5 days' then 1 else null end) as perf_5day_cnt,
		count(case when b.created_at <= a.created_at + interval '1 days' then 1 else null end) as perf_1day_cnt
	from my_performances a
		inner join my_performances b on b.fixed_title = a.fixed_title and b.created_at between a.created_at and a.created_at + interval '30 days'
	-- Exclude joins because that is not something I control and should not factor into favorite song
	where 	a.join_ind = 0
	and 	b.join_ind = 0
	group by 1,2, 3
	),
perf_stats as (
	select 	fixed_title, first_performance_time, current_month_ind,
			round(adj_perf_1day_cnt::decimal,2) as adj_perf_1day_cnt,
			round(adj_perf_5day_cnt::decimal,2) as adj_perf_5day_cnt,
			round(adj_perf_10day_cnt::decimal,2) as adj_perf_10day_cnt,
			round(adj_perf_30day_cnt::decimal,2) as adj_perf_30day_cnt,
			perf_30day_cnt, perf_10day_cnt, perf_5day_cnt, perf_1day_cnt, perf_cnt
	from 	(
				select 	fixed_title, min(created_at) as first_performance_time,
						case when to_char(max(created_at),'YYYY-MM') = to_char(current_timestamp,'YYYY-MM') then 1 else 0 end current_month_ind,
						max(perf_30day_cnt) as perf_30day_cnt,
						max(perf_10day_cnt) as perf_10day_cnt,
						max(perf_5day_cnt) as perf_5day_cnt,
						max(perf_1day_cnt) as perf_1day_cnt,
						max(perf_30day_cnt::float * adjust_rate) as adj_perf_30day_cnt,
						max(perf_10day_cnt::float * adjust_rate) as adj_perf_10day_cnt,
						max(perf_5day_cnt::float * adjust_rate) as adj_perf_5day_cnt,
						max(perf_1day_cnt::float * adjust_rate) as adj_perf_1day_cnt,
						count(*) as perf_cnt
				from 	perf_day_counts
				group by 1
			) a
	)
select 	ps.fixed_title, ps.first_performance_time, ps.perf_cnt,
		ps.perf_30day_cnt, ps.perf_10day_cnt, ps.perf_5day_cnt, ps.perf_1day_cnt,
		(
			(ps.adj_perf_1day_cnt::decimal*20) +
			(ps.adj_perf_5day_cnt::decimal*10) +
            (ps.adj_perf_10day_cnt::decimal*6) +
            (ps.adj_perf_30day_cnt::decimal*3) +
			(ps.perf_cnt::decimal)
		) adj_weighted_cnt,
		(
			(ps.perf_1day_cnt::decimal*20) +
			(ps.perf_5day_cnt::decimal*10) +
            (ps.perf_10day_cnt::decimal*6) +
            (ps.perf_30day_cnt::decimal*3) +
			(ps.perf_cnt::decimal)
		) weighted_cnt,
		ps.current_month_ind
from 	perf_stats ps
;
