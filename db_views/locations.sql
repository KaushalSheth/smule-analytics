CREATE OR REPLACE VIEW locations AS
with
all_locations as (
    select  owner_lat as lat, owner_lon as lon, orig_track_city as city, orig_track_country as country, count(*) as perf_cnt
    from    performance
    group by 1,2,3,4
    ),
preferred_location as (
    select  lat, lon, first_value(city) over w as city, first_value(country) over w as country, row_number() over w as rn
    from    all_locations
    window w as (partition by lat,lon order by perf_cnt desc)
    )
SELECT  lat, lon, city, country
FROM    preferred_location
where   rn = 1
;
