create or replace view my_repeat_analysis as
select  performers as main_performer,
        count(*) num_titles,
        sum(num_performances) as num_performances,
        sum(num_performances) - count(*) as repeats,
        count(case when num_performances > 1 then 1 else null end) as repeated_titles,
        max(num_performances) max_times
from (
    select performers,lpad(count(*)::varchar,2,'0') || '-' || fixed_title as title, count(*) as num_performances
    from my_performances
    group by performers,fixed_title
    ) a
group by 1
;
