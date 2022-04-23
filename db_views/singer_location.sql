drop view singer_location;
CREATE OR REPLACE VIEW singer_location AS
with max_perf as (select performers,max(created_at) as last_perf_time from my_performances group by 1)
select  s.*, calculate_distance(37.8,-121.9,s.lat,s.lon,'M') as miles_from_sr,
        g.city, g.country,
        case when (s.lat between 37.78 and 37.8) and (s.lon between -122.4 and -122.39) then true else false end as smule_hq_ind,
        case when (s.lat between 41.77 and 41.8) and (s.lon between -91.7 and -91.68) then true else false end as smule_midwest_ind,
        case when (s.lat between 20 and 20.1) and (s.lon between 77 and 77.1) then true else false end as smule_india_ind,
        case when (s.lat between 54 and 54.1) and (s.lon between -2 and -1.9) then true else false end as smule_uk_ind,
        p.last_perf_time
from    singer s
        inner join max_perf p on p.performers = s.performed_by
        left outer join geo_cache g on g.lat::float8 = s.lat and g.lon::float8 = s.lon
;
