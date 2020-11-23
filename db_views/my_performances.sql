CREATE OR REPLACE VIEW my_performances AS
WITH
perf AS (
    SELECT  p.*,
            split_part((p.key)::text, '_'::text, 1) AS instance_key
    FROM    performance p
    WHERE   1 = 1
    AND     exists (
                select  1
                from    performance_singer ps
                        inner join singer s on s.account_id = ps.singer_account_id and s.performed_by = 'KaushalSheth1'
                where   ps.performance_key = p.key
                )
    ),
title_stats AS (
    SELECT  p.fixed_title,
            lpad(count(*)::text,3,'0') as title_alltime_cnt,
            lpad(count(case when p.created_at > (now() - interval '30 days') then 1 else null end)::text,3,'0') as title_30day_cnt,
            lpad(count(case when p.created_at > (now() - interval '90 days') then 1 else null end)::text,3,'0') as title_90day_cnt
    FROM    perf p
    GROUP BY p.fixed_title
    ),
titles as (
    select  ts.fixed_title,
            ts.title_alltime_cnt || '-' || ts.title_30day_cnt || '-' || ts.title_90day_cnt || '-' || ts.fixed_title as title_alltime,
            ts.title_90day_cnt || '-' || ts.title_30day_cnt || '-' || ts.title_alltime_cnt || '-' || ts.fixed_title as title_90days,
            ts.title_30day_cnt || '-' || ts.title_90day_cnt || '-' || ts.title_alltime_cnt || '-' || ts.fixed_title as title_30days
    from    title_stats ts
),
partner_stats AS (
    SELECT  p.performers,
            lpad(count(*)::text,3,'0') as partner_alltime_cnt,
            lpad(count(case when p.created_at > (now() - interval '30 days') then 1 else null end)::text,3,'0') as partner_30day_cnt,
            lpad(count(case when p.created_at > (now() - interval '90 days') then 1 else null end)::text,3,'0') as partner_90day_cnt
    FROM    perf p
    GROUP BY p.performers
    ),
partners AS (
    SELECT  ps.performers,
            ps.partner_alltime_cnt || '-' || ps.partner_30day_cnt || '-' || ps.partner_90day_cnt || '-' || ps.performers as partner_alltime,
            ps.partner_90day_cnt || '-' || ps.partner_30day_cnt || '-' || ps.partner_alltime_cnt || '-' || ps.performers as partner_90days,
            ps.partner_30day_cnt || '-' || ps.partner_90day_cnt || '-' || ps.partner_alltime_cnt || '-' || ps.performers as partner_30days
    FROM    partner_stats ps
    ),
joiner_stats AS (
    SELECT  p.performers,
            lpad(count(*)::text,3,'0') as joiner_alltime_cnt,
            lpad(count(case when p.created_at > (now() - interval '7 days') then 1 else null end)::text,3,'0') as joiner_7day_cnt,
            lpad(count(case when p.created_at > (now() - interval '30 days') then 1 else null end)::text,3,'0') as joiner_30day_cnt,
            lpad(count(case when p.created_at > (now() - interval '90 days') then 1 else null end)::text,3,'0') as joiner_90day_cnt
    FROM    perf p
    where   p.owner_handle = 'KaushalSheth1'
    GROUP BY p.performers
    ),
joiners AS (
    SELECT  js.performers,
            js.joiner_alltime_cnt || '-' || js.joiner_7day_cnt || '-' || js.joiner_30day_cnt || '-' || js.joiner_90day_cnt || '-' || js.performers as joiner_alltime,
            js.joiner_90day_cnt || '-' || js.joiner_7day_cnt || '-' || js.joiner_30day_cnt || '-' || js.joiner_alltime_cnt || '-' || js.performers as joiner_90days,
            js.joiner_30day_cnt || '-' || js.joiner_7day_cnt || '-' || js.joiner_90day_cnt || '-' || js.joiner_alltime_cnt || '-' || js.performers as joiner_30days
    FROM    joiner_stats js
    )
SELECT  p.*,
        t.title_alltime,
        t.title_90days,
        t.title_30days,
        ptr.partner_alltime,
        ptr.partner_30days,
        ptr.partner_90days,
        j.joiner_alltime,
        j.joiner_30days,
        j.joiner_90days
FROM    perf p
        INNER JOIN partners ptr ON ptr.performers = p.performers
        INNER JOIN titles t ON t.fixed_title = p.fixed_title
        LEFT OUTER JOIN joiners j on j.performers = p.performers
;
