from .models import db
from .constants import *
from .db import execDBQuery
import pandas as pd
import seaborn as sb
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime

# Method to query title and partner analytics for a user
def fetchDBAnalytics(analyticsOptions): #analyticstitle,username,fromdate="2018-01-01",todate="2030-01-01"):
    global analytics, headings
    analytics = []
    headings = []
    # Extract variables from the options parameter for use later in the method
    analyticstitle = analyticsOptions['analyticstitle']
    username = analyticsOptions['username']
    fromdate = analyticsOptions['fromdate']
    todate = analyticsOptions['todate']
    timeperiod = analyticsOptions['timeperiod']
    # Build appropriate query based on analytics title passed in.  Set headings accordingly
    if analyticstitle == "Custom":
        headings = analyticsOptions['headings']
        sqlquery = analyticsOptions['analyticssql']
    elif analyticstitle in ['Partner Stats','Title Stats']:
        if analyticstitle == 'Partner Stats':
            selcol = "performers"
            col1alias = "user_search"
            col2alias = "title_search"
            listcol = "fixed_title"
            headcol1 = "Partner           "
            headcol2 = "First Title       "
            headcol3 = "# Titles"
            headcol4 = "Title List"
        else:
            selcol = "fixed_title"
            col1alias = "title_search"
            col2alias = "user_search"
            listcol = "performers"
            headcol1 = "Song Name         "
            headcol2 = "First Partner     "
            headcol3 = "# Partners"
            headcol4 = "Partner List"
        headings = [headcol1,'LastTime     ','First Time   ','Score',headcol2,headcol3,'# Perf','# Joins','P: 1st 30 Days','P: Last 30 Days', 'J: Last 30 days','Last Join Time',headcol4]
        # Build appropriate query
        # Start with the base query
        sqlquery = f"""
            with
            non_joiners as (select distinct performers from my_performances where join_ind = 0 order by 1),
            perf as (
                select  p.*, case when nj.performers is null then 0 else 1 end as non_joiner_ind
                from    my_performances p
                        left outer join non_joiners nj on nj.performers = p.performers
                where   p.created_at between '{fromdate}' and '{todate}'
                and     p.web_url not like '%ensembles'
                and     p.performers != '{username}'
                order by {selcol}
                ),
            perf_stats as (
                select  {selcol},
                        lpad((count(*) over w_list)::varchar,2,'0') || '-' || {listcol} as list_col,
                        first_value(created_at) over w_asc as first_performance_time,
                        first_value(created_at) over w_desc as last_performance_time,
                        first_value({listcol}) over w_asc as first_list_col,
                        count(1) over w_all as performance_cnt,
                        sum(join_ind) over w_all as join_cnt,
                        count(case when created_at > (now() - '30 days'::interval day) then 1 else null end) over w_all as perf_last_30_days,
                        sum(case when created_at > (now() - '30 days'::interval day) then join_ind else 0 end) over w_all as join_last_30_days,
                        max(case when join_ind = 1 then created_at else '2000-01-01'::timestamp end) over w_all as last_join_time
                from    perf
                where   1 = 1
                window  w_asc as (partition by {selcol} order by created_at),
                        w_desc as (partition by {selcol} order by created_at desc),
                        w_all as (partition by {selcol}),
                        w_list as (partition by {selcol},{listcol})
                order by {selcol}
                ),
            summary as (
                select  ps.{selcol},
                        min(ps.first_performance_time) as first_performance_time,
                        max(ps.last_performance_time) as last_performance_time,
                        max(ps.last_join_time) as last_join_time,
                        min(ps.first_list_col) as first_list_col,
                        min(ps.performance_cnt) as performance_cnt,
                        min(ps.join_cnt) as join_cnt,
                        min(ps.perf_last_30_days) as perf_last_30_days,
                        min(ps.join_last_30_days) as join_last_30_days,
                        string_agg(distinct ps.list_col,', ' order by ps.list_col desc) as join_list
                from    perf_stats ps
                group by 1
                )
            select  s.{selcol} as {col1alias}, s.last_performance_time, s.first_performance_time, coalesce(fp.recency_score, fs.adj_weighted_cnt, 0) as score, s.first_list_col as {col2alias},
                    (((length(s.join_list) - length(replace(s.join_list::varchar,', ',''))) / 2) + 1) as distinct_list_cnt,
                    case
                        when '{selcol}' = 'performers' then '<a href=http://localhost:3000/query_db_performances/user/' || s.{selcol} || ' target="_blank">' || s.performance_cnt || '</a>'
                        else '<a href=http://localhost:3000/query_db_performances/title/' || replace(s.{selcol},' ','_') || ' target="_blank">' || s.performance_cnt || '</a>'
                    end as performance_link_str,
                    case
                        when '{selcol}' = 'performers' then '<a href=http://localhost:3000/query_db_performances/joins/' || s.{selcol} || ' target="_blank">' || s.join_cnt || '</a>'
                        else '<a href=http://localhost:3000/query_db_performances/titlejoins/' || replace(s.{selcol},' ','_') || ' target="_blank">' || s.join_cnt || '</a>'
                    end as join_link_str,
                    count(case when date_part('day',p.created_at - s.first_performance_time) < 30 then 1 else null end) as perf_first_30_days,
                    s.perf_last_30_days, s.join_last_30_days, s.last_join_time, s.join_list
            from    summary s
                    -- Only include performers I've joined - exclude joiners whom I have not joined
                    inner join perf p on p.{selcol} = s.{selcol} and ('{selcol}' != 'performers' or p.non_joiner_ind = 1)
                    left outer join favorite_partner fp on fp.partner_name = s.{selcol}
                    left outer join favorite_song fs on fs.fixed_title = s.{selcol}
            group by 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13
            order by 2 desc
            """
    elif analyticstitle == 'Invite':
        headings = [\
            'Song Name', 'Rating', 'Invite Score', 'Fav Score', 'Random Sort', 'Singer Type', 'Artist', \
            '# Perf', '# Partners', '# Invites', '# Joins', 'Join Ratio', 'First Perf', 'Last Perf', 'Last Invite'\
            ]
        sqlquery = f"""
            select  fixed_title as title_search, 'T:' || lpad(rating_nbr::varchar,2,'0') as rating_nbr, invite_recency_score, favorite_score_nbr, round(random()::decimal,4)*100 as random_sort_nbr,
                    coalesce(singer_type,'') as singer_type, coalesce(artist,'') as artist,
                    '<a href=http://localhost:3000/query_db_performances/title/' || replace(fixed_title,' ','_') || ' target="_blank">' || num_all_performances || '</a>' as performance_link_str,
                    num_partners, num_invites, num_joins,
                    round(case when num_invites > 0 then num_joins*1.0/num_invites else 0 end,2) as join_ratio,
                    first_performance_time, last_performance_time, last_invite_time
            from    my_invite_analysis
            where   fixed_title not in (select item_name from smule_list where list_type = 'EXCLUDE_INVITE_ANALYTICS')
            """
    elif analyticstitle == 'Repeat':
        headings = ['Main Performer', 'Song Name', '# Performances', 'First Performed', 'Last Performed']
        sqlquery = f"""
            select  performers as user_search, fixed_title as title_search, count(*) num_performances, min(created_at) as first_performance_time, max(created_at) as last_performance_time
            from    my_performances
            where   created_at between '{fromdate}' and '{todate}'
            and     performers != '{username}'
            group by 1,2
            having count(*) > 1
            order by 3 desc
            """
    elif analyticstitle == 'Favorite Songs':
        headings = ['Song Name', 'Current Month', '3 months', 'Rating', 'Adjusted Weighted Count', 'Random Sort', 'Type', 'Singer(s)', 'First Perf Time', 'Last Perf Time', '# Performances', '# Partners', '# Joiners', '# Invites', '# Joins', 'Last Join Time', '# Perf - 1 Day', '# Perf - 5 Days', '# Perf - 10 Days', '# Perf - 30 Days']
        sqlquery = f"""
            select  fixed_title as title_search, current_month_ind, past_3mo_ind, 'T:' || lpad(coalesce(rating_nbr,0)::varchar,2,'0') as rating_nbr, adj_weighted_cnt,
                    case when rating_nbr >= 9 then 'R1:' when rating_nbr >= 7 then 'R2:' else 'R3:' end || round(random()::decimal,4) as random_sort_nbr,
                    coalesce(singer_type,'') as singer_type, coalesce(artist,''), first_performance_time, last_performance_time,
                    '<a href=http://localhost:3000/query_db_performances/title/' || replace(fixed_title,' ','_') || ' target="_blank">' || perf_cnt || '</a>' as performance_link_str,
                    partner_cnt, joiner_cnt, invite_cnt, join_cnt, last_join_time,
                    perf_1day_cnt, perf_5day_cnt, perf_10day_cnt, perf_30day_cnt
            from    favorite_song
            order by current_month_ind, coalesce(rating_nbr,0) desc, adj_weighted_cnt desc
            """
    elif analyticstitle == 'Favorite Partners':
        headings = ['Partner', 'Recency Score', 'Avg Rating', 'Last 10 Rating', 'Random Sort', 'Perf/Join', 'Fav/Perf', '# First Partner', 'First Perf Time', '# Perf', '# Titles', 'Title/Perf', '# Joins', '# Fav', 'Last Perf Time', '# Perf 14 Days', '# Join 30 Days', 'Following', '# Days Till First Join', 'First Join Time', 'Last Join Time', '# Rated']
        sqlquery = f"""
            select  partner_name as user_search,
                    round(case when recency_score = 99999 then 0 else recency_score end, 2) as recency_score,
                    avg_rating_nbr as rating, last10_rating_str,
                    case when last10_nine_cnt >= 10 then 'R1:' when last10_nine_cnt >= 8 then 'R2:' when last10_nine_cnt >= 6 then 'R3:' when last10_nine_cnt >= 4 then 'R4:' else 'R5:' end || round(random()::decimal,4) as random_sort_nbr,
                    --round(case when rating = 99999 then 0 else rating end, 2) as rating,
                    case when join_cnt = 0 then null else round(performance_cnt/(join_cnt*1.0),2) end as perf_join_ratio,
                    case when performance_cnt = 0 then null else round(favorite_cnt/(performance_cnt*1.0),2) end as fav_perf_ratio,
                    first_partner_cnt,
                    first_performance_time,
                    '<a href=http://localhost:3000/query_db_performances/user/' || partner_name || ' target="_blank">' || performance_cnt || '</a>' as performance_link_str,
                    title_cnt,
                    case when performance_cnt = 0 then null else round(title_cnt/(performance_cnt*1.0),2) end as title_perf_ratio,
                    '<a href=http://localhost:3000/query_db_performances/joins/' || partner_name || ' target="_blank">' || join_cnt || '</a>' as join_link_str,
                    '<a href=http://localhost:3000/query_db_favorites/' || partner_name || ' target="_blank">' || favorite_cnt || '</a>' as favorite_link_str,
                    last_performance_time, performance_last_14_days_cnt, join_last_30_days_cnt, is_following,
                    days_till_first_join, first_join_time, last_join_time, rated_song_cnt
            from    favorite_partner
            where   performance_cnt > 1
            order by recency_score desc
            """
    elif analyticstitle == 'Period Stats':
        headings = ['#','Period',\
                    '# Perf','# Invites','# Joins','Joins Per Invite','Join %','Unique Titles','Unique %','New Titles','Unique Partners','New Partners','New Joiners',\
                    'Total Perf','Total Invites','Total Joins','Total Titles','Total Partners','Total Joiners']
        sqlquery = f"""
            with
            perf as (select * from my_performances where created_at between '{fromdate}' and '{todate}'),
            title_stats as (
            	select first_perf_period, count(*) as new_title_cnt
            	from (
            		select 	fixed_title,
            				to_char(min(created_at),'{timeperiod}') as first_perf_period
            		from 	perf
            		group by 1
            		) a
            	group by 1
            	),
                partner_dates as (
            		select 	performers,
            				to_char(min(created_at),'{timeperiod}') as first_perf_period,
                            to_char(min(case when join_ind = 1 then created_at else null end),'{timeperiod}') as first_join_period
            		from 	perf
            		group by 1
                    ),
            partner_stats as (
            	select first_perf_period, count(*) as new_partner_cnt
            	from partner_dates
            	group by 1
            	),
            joiner_stats as (
            	select first_join_period, count(*) as new_joiner_cnt
            	from partner_dates
            	group by 1
                ),
            perf_stats as (
            	select 	to_char(created_at,'{timeperiod}') perf_period,
            			count(*) as perf_cnt,
            			count(distinct performers) as partner_cnt,
            			count(distinct fixed_title) as title_cnt,
            			sum(invite_ind) invite_cnt,
            			count(case when join_ind = 1 and performers != 'KaushalSheth1' then 1 else null end) as join_cnt
            	from 	perf
            	group by 1
            	)
            select 	row_number() over() as rownum,
                    ps.perf_period,
            		to_char(ps.perf_cnt,'9,999') as perf_cnt,
            		ps.invite_cnt,
            		ps.join_cnt,
            		round(case when ps.invite_cnt > 0 then (1.0*ps.join_cnt/ps.invite_cnt) else 0.0 end,2) as join_per_invite_cnt,
            		round(case when ps.join_cnt > 0 then (1.0*ps.join_cnt/ps.perf_cnt) else 0.0 end * 100,2) as join_performance_pct,
                    ps.title_cnt,
                    round((1.0*ps.title_cnt/(ps.perf_cnt-coalesce(ps.join_cnt,0))) * 100,2) as unique_title_pct,
            		ts.new_title_cnt,
                    ps.partner_cnt,
            		ptrs.new_partner_cnt,
            		js.new_joiner_cnt,
            		to_char(sum(ps.perf_cnt) over(order by ps.perf_period),'99,999') as total_perf_cnt,
            		to_char(sum(ps.invite_cnt) over(order by ps.perf_period),'99,999') as total_invite_cnt,
            		to_char(sum(ps.join_cnt) over(order by ps.perf_period),'99,999') as total_join_cnt,
            		to_char(sum(ts.new_title_cnt) over(order by ts.first_perf_period),'99,999') as total_title_cnt,
            		to_char(case when ptrs.new_partner_cnt is not null then sum(ptrs.new_partner_cnt) over(order by ptrs.first_perf_period) end,'99,999') as total_partner_cnt,
            		to_char(case when js.new_joiner_cnt is not null then sum(js.new_joiner_cnt) over(order by js.first_join_period) end,'99,999') as total_joiner_cnt
            from 	perf_stats ps
            		left outer join title_stats ts on ts.first_perf_period = ps.perf_period
            		left outer join partner_stats ptrs on ptrs.first_perf_period = ps.perf_period
                    left outer join joiner_stats js on js.first_join_period = ps.perf_period
            order by 2 desc;
            """
    elif analyticstitle in ['Partner Heatmap','Title Heatmap','Joiner Heatmap','Favorites Heatmap']:
        # Set default values for left, top and right margin - these can be overridden for individual heatmaps in the relevant section if needed
        leftmgn = 0.14
        topmgn = 0.96
        rightmgn = 1.0
        if analyticstitle == 'Partner Heatmap':
            outhead = "Partner Name"
            selcol = "performers"
            outcol = "partner_name"
            extrawhere = ""
        elif analyticstitle == 'Joiner Heatmap':
            outhead = "Joiner Name"
            selcol = "performers"
            outcol = "joiner_name"
            extrawhere = "and join_ind = 1"
        elif analyticstitle == 'Title Heatmap':
            outhead = "Title"
            selcol = "fixed_title"
            outcol = "fixed_title"
            extrawhere = ""
            # Titles are longer than partner names, so increase left margin
            leftmgn = 0.212
        elif analyticstitle == 'Favorites Heatmap':
            outhead = "Partner Name"
            selcol = "performers"
            outcol = "partner_name"
            extrawhere = "and favorite_ind = 1"
        headings = [outhead,'Perf Month','Perf Count']
        sqlquery = f"""with
            -- Set start date to 12 months ago
            dates as (select date_trunc('MON',now()) - interval '13 months' as start_ts, date_trunc('MON',now()) - interval '1 second' as end_ts),
            perf as (select mp.* from my_performances mp inner join dates on mp.created_at between dates.start_ts and dates.end_ts where performers not in ('KaushalSheth1','HMA_Official') {extrawhere}),
            -- Select top 50 partners/joiners/titles with max # performances since start date
            counts as (
                select  {selcol} as count_column, {selcol} || ' (' || round(avg(rating_nbr)*20,0) || ')' as display_column, count(*) as total_perf_cnt
                from    perf
                group by 1
                order by 3 desc
                limit 50
                )
            select  c.display_column as {outcol}, to_char(mp.created_at,'YYYY-MM') as perf_month, count(*) as perf_cnt
            from    perf mp
                    inner join counts c on c.count_column = mp.{selcol}
            where   1 = 1
            -- For Title heatmap, exclude joins as that skews the numbers drastically
            and     0 = case when '{selcol}' = 'fixed_title' then mp.join_ind else 0 end
            group by 1,2
            order by 2 desc, 3 desc
            """
        df = pd.read_sql_query(sqlquery,db.session.connection())
        # Create pivot table with {outcol} values as rows, month as columns, and perf_cnt as values
        sbdf = df.pivot(index=outcol,columns='perf_month',values='perf_cnt')
        # Generate heatmap of appropriate size and margins, and set title according to name of heatmap being generated
        sb.heatmap(sbdf, annot=True, fmt="g", cmap="viridis", yticklabels=True)
        plt.gcf().set_size_inches(15,11)
        plt.subplots_adjust(left=leftmgn,top=topmgn,right=rightmgn)
        plt.title(analyticstitle + " - " + datetime.now().strftime("%Y/%m/%d"))
        plt.show()

    #print(sqlquery)
    # Execute the query and build the analytics list
    analytics = execDBQuery(sqlquery)
    return headings,analytics
