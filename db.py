from .models import db, Performance, Singer, PerformanceSinger, PerformanceFavorite, TitleMapping, SingerFollowing, GeoCache
from .utils import fix_title,build_comment
from sqlalchemy import text, Table, Column
import copy

# Method to feth Title Mappings
def fetchDBTitleMappings():
    global titleMappings
    titleMappings = dict()
    result = db.session.execute("select smule_title,mapped_title from title_mapping order by length(smule_title) desc")
    for r in result:
        titleMappings[r['smule_title']] = r['mapped_title']
    return titleMappings

# Calculate and return date difference
def dateDelta(input_date,deltaStr,deltaOp='+'):
    calc_date = null
    # First, separate the numeric and non-numeric portion of string to determine hour, day, month or year
    deltaNum = ""
    period = ""
    for c in deltaStr:
        if not c.isdigit:
            period += c
        else:
            deltaNum += c
    # Fix the periods to valid postgres values
    if period == "h":
        period = "hour"
    elif period == "d":
        period = "day"
    elif period == "mo":
        period = "month"
    elif period == "yr":
        period = "year"
    # Build the query and execute it to get the result
    query = f"select '{input_date}'::timestamp {deltaOp} '{deltaNum} {period}' as calc_date"
    result = db.session.execute(query)
    for r in result:
        calc_date = r['calc_date']
    # Return the calculated date
    return calc_date

# Method to fix DB Titles using title Mappings
def fixDBTitles(titleMappings):
    fixCount = 0
    # Define a title mapping table with the data in the dict sent in
    tblTitleMapping = Table("title_mapping", db.metadata,
        Column("smule_title", db.String(100), primary_key=True),
        Column("mapped_title", db.String(100)),
        extend_existing=True,
        )
    # Truncate teh table and load all titleMappings into the table
    result = db.session.execute('truncate table title_mapping')
    result = db.session.execute(tblTitleMapping.insert().values([{"smule_title": s, "mapped_title": m} for s,m in titleMappings.items()]))
    # Update rows where title matches a row in temp table
    updateSQL = """
    update  performance p
    set     fixed_title = tm.mapped_title,
            filename = replace(filename,tm.smule_title,tm.mapped_title),
            updated_at = now()
    from    title_mapping tm
    where   p.fixed_title = tm.smule_title
    and     p.fixed_title != tm.mapped_title
    """
    fixCount = db.session.execute(updateSQL).rowcount
    print(f"Rows updated = {fixCount}")
    db.session.commit()

    return fixCount

# Method to query performers
def fetchDBPerformers(fromdate="2018-01-01",todate="2030-01-01"):
    performers = []
    sqlquery = f"""
        select * from (
            select  p.performers, s.pic_url as display_pic_url,
                    substr(p.joiner_7days,1,15) as joiner_stats,
                    substr(p.partner_30days,1,11) as partner_stats,
                    first_value(p.created_at) over w as last_performance_time,
                    l.city,
                    l.country,
                    row_number() over w as rn
            from    my_performances p
                    inner join singer s on s.performed_by = p.performers
                    left outer join locations l on l.lat = s.lat and l.lon = s.lon
            where   p.created_at between '{fromdate}' and '{todate}'
            window w as (partition by p.performers order by case when p.owner_handle = 'KaushalSheth1' then '2000-01-01'::timestamp else p.created_at end desc, p.created_at desc)
            ) a
        where a.rn = 1
        order by case when joiner_stats is null then '0' else '1' end, replace(performers,'_','0')
        """
    # Execute the query and build the performers list
    performers = execDBQuery(sqlquery)
    return performers

def fetchDBTopPerformers():
    performers = []
    sqlquery = f"""
        with
        perf as (
        	select 	*, date_trunc('MON',created_at) as perf_month
        	from 	my_performances
        	-- Ignore joins - only want to count performances that I have joined
        	where 	join_ind = 0
        	and 	performers != 'KaushalSheth1'
        	-- Look at the last 20 months ending last month
        	and 	created_at >= date_trunc('MON',current_timestamp) - interval '20 months'
        	and 	created_at < date_trunc('MON',current_timestamp)
        	),
        perf_counts as (
        	select 	perf_month, performers, owner_account_id, count(*) perf_cnt
        	from 	perf
        	group by 1,2,3 order by 1,4 desc
        	),
        perf_ranked as (
        	select	*,
        			row_number() over(partition by perf_month order by perf_cnt desc) as monthly_rank
        	from 	perf_counts
        	)
        select 	pr.*, s.pic_url, to_char(perf_month,'Mon YYYY') as perf_month_str
        from 	perf_ranked pr
        		inner join singer s on s.account_id = pr.owner_account_id
        where 	monthly_rank <= 10
        order by monthly_rank, perf_month desc;
        """
    # Execute the query and build the performers list
    performers = execDBQuery(sqlquery)
    return performers

# Method to execute specified query and return result as a list of rows
def execDBQuery(sqlquery):
    results = []
    # Some queries (like updates) don't return any results, so catch and ignore those errors
    try:
        result = db.session.execute(sqlquery)
        for r in result:
            # Convert the result row into a dict we can add to performances
            d = r._asdict()
            results.append(d)
    except Exception as e:
        # If an exception happened, we likely executed an INSERT or UPDATE, so commit it
        db.session.commit()
    return results

# Method to query performances for a user
def fetchDBJoiners(username,fromdate="2018-01-01",todate="2030-01-01"):
    joiners = []
    sqlquery = f"""
        select  distinct p.performers as joiner
        from    performance p
        where   p.owner_handle = '{username}'
        and     p.created_at between '{fromdate}' and '{todate}'
        and     p.performers != '{username}'
        order by 1
        """
    # Execute the query and build the joiners list
    joiners = execDBQuery(sqlquery)
    return joiners

# Method to query performances for a user
def fetchDBPerformances(username,maxperf=9999,fromdate="2018-01-01",todate="2030-01-01",titleMappings=[],searchOptions={'dbfilter':"1=1"}):
    global performances
    performances = []
    i = 0

    # Build base query
    sqlquery = f"""
        select  p.*
        from    all_performances p
        where   p.created_at between '{fromdate}' and '{todate}'
        and     p.performer_handles ilike '%{username}%'
        and     p.web_url not like '%ensembles'
        """
    # Check if there is any dbfilter to be added and if so, add it to the query
    dbfilter = searchOptions['dbfilter']
    if dbfilter != "":
        sqlquery += " and " + dbfilter
    # Append ORDER BY clause - but only if the dbfilter does not already contain an ORDER BY clause
    if "order by" not in dbfilter.lower():
        sqlquery += " order by created_at desc"

    # Check the PerformanceSinger table for existence of the singer on the performance
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = r._asdict()
        # Convert created_at to string
        d['created_at'] = d['created_at'].strftime("%Y-%m-%dT%H:%M:%S")
        # Add the keys to the dict that are not saved to the DB but used for other processing
        d['other_performers'] = ""
        d['pic_filename'] = ""
        d['create_type'] = ""
        d['joiners'] = ""
        d['web_url_full'] = d['web_url']
        d['recording_url'] = d['web_url'].replace("/ensembles","")
        d['yt_search'] = "https://www.youtube.com/results?search_query=" + d['fixed_title'].replace(" ","+") + "+lyrics"
        # Set display handle and pic_url based on user we are searching for
        if d['owner_handle'] == username:
            d['display_handle'] = d['partner_name']
            d['display_pic_url'] = d['partner_pic_url']
            # Construct comment for joiner
            d['comment'] = build_comment('@' + d['display_handle'] + ' thanks for joining...')
        else:
            d['display_handle'] = d['owner_handle']
            d['display_pic_url'] = d['owner_pic_url']
            # Construct comment for partner
            d['comment'] = build_comment('@' + d['display_handle'] + ' ', " Please check my Favorites for all my recent invites and join the ones you like")
        performances.append(d)
        i += 1
        if i >= maxperf:
            break

    return performances

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
            perf as (select * from my_performances where created_at between '{fromdate}' and '{todate}' and web_url not like '%ensembles' and performers != '{username}'),
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
                from    my_performances
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
                    s.performance_cnt, s.join_cnt,
                    count(case when date_part('day',p.created_at - s.first_performance_time) < 30 then 1 else null end) as perf_first_30_days,
                    s.perf_last_30_days, s.join_last_30_days, s.last_join_time, s.join_list
            from    summary s
                    inner join perf p on p.{selcol} = s.{selcol}
                    left outer join favorite_partner fp on fp.partner_name = s.{selcol}
                    left outer join favorite_song fs on fs.fixed_title = s.{selcol}
            group by 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13
            order by 2 desc
            """
    elif analyticstitle == 'Invite':
        headings = [\
            'Song Name', 'Total Score', 'Invite Score', 'Favorite Score', 'Popularity Score', 'First Performance Score', \
            'Last Performance Score', '# Performances', '# Partners', '# Invites', '# Joins', 'First Performance', 'Last Performance'\
            ]
        sqlquery = f"""
            select  fixed_title as title_search, total_score, invite_recency_score, favorite_score_nbr, popularity_score,
                    first_performance_score, performance_recency_score, num_all_performances, num_partners, num_invites,
                    num_joins, first_performance_time, last_performance_time
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
        headings = ['Song Name', 'Current Month', 'Adjusted Weighted Count', 'Weighted Count', 'First Perf Time', '# Performances', '# Perf - 1 Day', '# Perf - 5 Days', '# Perf - 10 Days', '# Perf - 30 Days']
        sqlquery = f"""
            select  fixed_title as title_search, current_month_ind, adj_weighted_cnt, weighted_cnt, first_performance_time, perf_cnt, perf_1day_cnt, perf_5day_cnt, perf_10day_cnt, perf_30day_cnt
            from    favorite_song
            order by adj_weighted_cnt desc
            """
    elif analyticstitle == 'Favorite Partners':
        headings = ['Partner', 'Recency Score', 'Rating', 'Perf/Join Ratio', 'First Perf Time', '# Performances', '# Joins', '# Favorites', 'Last Perf Time', '# Perf 14 Days', '# Join 30 Days', 'Following']
        sqlquery = f"""
            select  partner_name as user_search,
                    round(case when recency_score > 100000 then recency_score - 100000 when recency_score = 99999 then 0 else recency_score end, 2) as recency_score,
                    round(case when rating = 99999 then 0 else rating end, 2) as rating,
                    case when (join_cnt = 0 or join_cnt < performance_cnt/20.0) then round(performance_cnt/10.0,2) else round(performance_cnt/join_cnt,2) end as perf_join_ratio,
                    first_performance_time, performance_cnt, join_cnt, favorite_cnt, last_performance_time, performance_last_14_days_cnt, join_last_30_days_cnt, is_following
            from    favorite_partner
            order by recency_score desc
            """
    elif analyticstitle == 'Period Stats':
        headings = ['#','Period','# Performances','Total Performances','# Invites','Total Invites','# Joins','Total Joins','Joins Per Invite','Join %',\
                    'Unique Titles','New Titles','Total Titles','Unique Partners','New Partners','Total Partners','New Joiners','Total Joiners']
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
            		to_char(sum(ps.perf_cnt) over(order by ps.perf_period),'99,999') as total_perf_cnt,
            		ps.invite_cnt,
            		to_char(sum(ps.invite_cnt) over(order by ps.perf_period),'99,999') as total_invite_cnt,
            		ps.join_cnt,
            		to_char(sum(ps.join_cnt) over(order by ps.perf_period),'99,999') as total_join_cnt,
            		round(case when ps.invite_cnt > 0 then (1.0*ps.join_cnt/ps.invite_cnt) else 0.0 end,2) as join_per_invite_cnt,
            		round(case when ps.join_cnt > 0 then (1.0*ps.join_cnt/ps.perf_cnt) else 0.0 end * 100,2) as join_performance_pct,
                    ps.title_cnt,
            		ts.new_title_cnt,
            		to_char(sum(ts.new_title_cnt) over(order by ts.first_perf_period),'99,999') as total_title_cnt,
                    ps.partner_cnt,
            		ptrs.new_partner_cnt,
            		to_char(case when ptrs.new_partner_cnt is not null then sum(ptrs.new_partner_cnt) over(order by ptrs.first_perf_period) end,'99,999') as total_partner_cnt,
            		js.new_joiner_cnt,
            		to_char(case when js.new_joiner_cnt is not null then sum(js.new_joiner_cnt) over(order by js.first_join_period) end,'99,999') as total_joiner_cnt
            from 	perf_stats ps
            		left outer join title_stats ts on ts.first_perf_period = ps.perf_period
            		left outer join partner_stats ptrs on ptrs.first_perf_period = ps.perf_period
                    left outer join joiner_stats js on js.first_join_period = ps.perf_period
            order by 2 desc;
            """
    #print(sqlquery)
    # Execute the query and build the analytics list
    analytics = execDBQuery(sqlquery)
    return headings,analytics

# Save the performances queried from Smule to the DB
def saveDBPerformances(username,performances):
    i = 0
    # Need to use deepcopy to copy the list of objects so that the original list does not get overwritten
    db_performances = copy.deepcopy(performances)
    # Loop through each performance that has been queried
    for p in db_performances:
        # Use a try block because we want to ignore performances with bad data
        # If any error occurs when processing the performance, simply skip it
        # TODO: Use more granular error checks
        try:
            # The other_performers list is not part of the Performance class, so extract it to a variable and delete from the record
            other_performers = p['other_performers']
            del p['other_performers']
            # Delete performers and pic_filename as well since that is not part of the DB table
            del p['pic_filename']
            del p['partner_name']
            del p['display_handle']
            del p['display_pic_url']
            del p['create_type']
            del p['joiners']
            del p['recording_url']
            del p['comment']
            del p['yt_search']
            del p['web_url_full']
            del p['rating_nbr']

            # Create/Update the Singer record for the performance owner
            # Note that the pic, lat and lon for the owner will be updated to the last performance processed
            # TODO: Consider saving a history of pic, lat and lon for each singer
            singer = Singer(\
                        account_id = p['owner_account_id'],\
                        performed_by = p['owner_handle'],\
                        pic_url = p['owner_pic_url'],\
                        lat = p['owner_lat'],\
                        lon = p['owner_lon']\
                        )
            db.session.merge(singer)

            # Convert the performance record to the Performance class for SQLAlchemy and merge with the performances queried from DB
            np = Performance(**p)
            db.session.merge(np)

            # Process the PerformanceSinger record for the owner of the performance
            perfSinger = PerformanceSinger(\
                        performance_key = p['key'],\
                        singer_account_id = p['owner_account_id']\
                        )
            db.session.merge(perfSinger)

            # Loop through all the other performers in the performance and process the Singer and PerformanceSinger records for them
            for o in other_performers:
                # Note that for other performers, we don't get lat/lon values, which is why they are not defined as required columns
                singer = Singer(\
                            account_id = o['account_id'],\
                            performed_by = o['handle'],\
                            pic_url = o['pic_url']\
                            )
                db.session.merge(singer)
                perfSinger = PerformanceSinger(\
                            performance_key = p['key'],\
                            singer_account_id = o['account_id']\
                            )
                db.session.merge(perfSinger)
            # Commit all the changes for the performance if no errors were encountered
            db.session.commit()
            i += 1
        except:
            # If any errors are encountered for the performance, roll back all DB changes made for that performance
            db.session.rollback()
            # Uncomment following line for debugging purposes only
            raise

    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(performances)} performances processed"

# Save the favorite performances using performance key and other attributes
def saveDBFavorite(username,performanceKey,rating):
    # Use a try block because we want to ignore performances with bad data
    # If any error occurs when processing the performance, simply skip it
    # TODO: Use more granular error checks
    try:
        # Process the PerformanceSinger record for the owner of the performance
        perfFavorite = PerformanceFavorite(\
                    favorited_by_username = username,\
                    performance_key = performanceKey,\
                    rating_nbr = rating\
                    )
        db.session.merge(perfFavorite)
        # Commit all the changes for the performance if no errors were encountered
        db.session.commit()
        retVal = 1
    except:
        # If any errors are encountered for the performance, roll back all DB changes made for that performance
        db.session.rollback()
        retVal = 0
        # Uncomment following line for debugging purposes only
        #raise
    return retVal

# Save GeoCache data
def saveDBGeoCache(lat,lon,city,country):
    # Use a try block because we want to ignore bad data
    # If any error occurs when processing the GeoCache, simply skip it
    try:
        # Process the PerformanceSinger record for the owner of the performance
        geoCache = GeoCache(\
                    lat = lat,\
                    lon = lon,\
                    city = city[:40],\
                    country = country[:40]\
                    )
        db.session.merge(geoCache)
        # Commit all the changes for the performance if no errors were encountered
        db.session.commit()
        retVal = 1
    except:
        # If any errors are encountered for the performance, roll back all DB changes made for that performance
        db.session.rollback()
        retVal = 0
        # Uncomment following line for debugging purposes only
        raise
    return retVal

# Save the favorite performances using the performance list queried from Smule
def saveDBFavorites(username,performances):
    i = 0
    # Loop through each performance that has been queried
    for p in performances:
        i += saveDBFavorite(username,p['key'],5)
    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(performances)} favorites processed"

# Insert/Update data into Singer_Following table
def saveDBSingerFollowing(userFollowing):
    i = 0
    # First, update all rows to set isFollowing to False
    # TODO: Since we seem to be getting partial lists, disable setting is_following to false - we will handle that manually in DB directly when needed
    #db.session.execute("update singer_following set is_following = False, updated_at = now() where is_following")
    # Next, loop through and insert/update all the rows
    for u in userFollowing:
        # It is possible that first_name and or last_name are missing - in that case, simply set them to ""
        try:
            first_name = u['first_name']
        except:
            first_name = ""
        try:
            last_name = u['last_name']
        except:
            last_name = ""
        handle = u['handle']
        is_following = True

        # Use a try block because we want to ignore bad data
        # If any error occurs when processing the user, simply skip it
        # TODO: Use more granular error checks
        try:
            # Process the PerformanceSinger record for the owner of the performance
            sf = SingerFollowing(\
                        account_id = u['account_id'],\
                        handle = handle,\
                        url = u['url'],\
                        first_name = first_name,\
                        last_name = last_name,\
                        pic_url = u['pic_url'],\
                        is_following = is_following,\
                        is_vip = u['is_vip'],\
                        is_verified = u['is_verified'],\
                        verified_type = u['verified_type'],\
                        )
            db.session.merge(sf)
            # Commit all the changes for the performance if no errors were encountered
            db.session.commit()
            i += 1
        except:
            # If any errors are encountered for the performance, roll back all DB changes made for that performance
            db.session.rollback()
            # Uncomment following line for debugging purposes only
            raise

    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(userFollowing)} SingerFollowing processed"
