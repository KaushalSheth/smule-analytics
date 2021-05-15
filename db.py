from .models import db, Performance, Singer, PerformanceSinger, PerformanceFavorite, TitleMapping, SingerFollowing
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
    # Define a title mapping temp table with the data in the dict sent in
    tblTitleMapping = Table("tmp_title_mapping", db.metadata,
        Column("smule_title", db.String(100)),
        Column("mapped_title", db.String(100)),
        extend_existing=True,
        )
    # Create the temp table
    tblTitleMapping.create(bind=db.session.get_bind())
    # Insert all titleMappings into the table
    result = db.session.execute(tblTitleMapping.insert().values([{"smule_title": s, "mapped_title": m} for s,m in titleMappings.items()]))
    # Update rows where title matches a row in temp table
    updateSQL = """
    update  performance p
    set     fixed_title = tmp.mapped_title,
            filename = replace(filename,tmp.smule_title,tmp.mapped_title),
            updated_at = now()
    from    tmp_title_mapping tmp
    where   p.fixed_title = tmp.smule_title
    and     p.fixed_title != tmp.mapped_title
    """
    fixCount = db.session.execute(updateSQL).rowcount
    print(f"Rows updated = {fixCount}")
    db.session.commit()
    tblTitleMapping.drop(bind=db.session.get_bind())

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
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        performers.append(d)
    return performers

# Method to execute specified query and return result as a list of rows
def execDBQuery(sqlquery):
    results = []
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        results.append(d)
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
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        joiners.append(d)
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
    # Append ORDER BY clause
    sqlquery += " order by created_at desc"

    # Check the PerformanceSinger table for existence of the singer on the performance
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
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
            d['filename'] = "(JOIN) " + d['filename']
            # Construct comment for joiner
            d['comment'] = build_comment('@' + d['display_handle'] + ' thanks for joining...')
        else:
            d['display_handle'] = d['owner_handle']
            d['display_pic_url'] = d['owner_pic_url']
            # Construct comment for partner
            d['comment'] = build_comment('@' + d['display_handle'] + ' thanks for the invite...')
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
    # Build appropriate query based on analytics title passed in.  Set headings accordingly
    if analyticstitle == "Custom":
        headings = analyticsOptions['headings']
        sqlquery = analyticsOptions['analyticssql']
    elif analyticstitle in ['Partner Stats','Title Stats']:
        if analyticstitle == 'Partner Stats':
            headings = ['Partner           ','LastTime     ','First Time   ','First Title      ','# Perf','# Joins','P: 1st 30 Days','P: Last 30 Days', 'J: Last 30 days','Title List']
            selcol = "performers"
            listcol = "fixed_title"
        else:
            headings = ['Song Name         ','Last Time     ','First Time   ','First Partner   ','# Perf','# Joins','P: 1st 30 Days','P: Last 30 Days', 'J: Last 30 days','Partner List']
            selcol = "fixed_title"
            listcol = "performers"
        # Build appropriate query
        # Start with the base query
        sqlquery = f"""
            with
            perf as (select * from my_performances where created_at between '{fromdate}' and '{todate}' and web_url not like '%ensembles'),
            perf_stats as (
                select  {selcol},
                        lpad((count(*) over w_list)::varchar,2,'0') || '-' || {listcol} as list_col,
                        first_value(created_at) over w_asc as first_performance_time,
                        first_value(created_at) over w_desc as last_performance_time,
                        first_value({listcol}) over w_asc as first_list_col,
                        count(1) over w_all as performance_cnt,
                        count(case when owner_handle = 'KaushalSheth1' and web_url not like '%ensembles' then 1 else null end) over w_all as join_cnt,
                        count(case when created_at > (now() - '30 days'::interval day) then 1 else null end) over w_all as perf_last_30_days,
                        count(case when owner_handle = 'KaushalSheth1' and web_url not like '%ensembles' and created_at > (now() - '30 days'::interval day) then 1 else null end) over w_all as join_last_30_days
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
                        min(ps.first_list_col) as first_list_col,
                        min(ps.performance_cnt) as performance_cnt,
                        min(ps.join_cnt) as join_cnt,
                        min(ps.perf_last_30_days) as perf_last_30_days,
                        min(ps.join_last_30_days) as join_last_30_days,
                        string_agg(distinct ps.list_col,', ' order by ps.list_col desc) as join_list
                from    perf_stats ps
                group by 1
                )
            select  s.{selcol} as search_text, s.last_performance_time, s.first_performance_time, s.first_list_col, s.performance_cnt, s.join_cnt,
                    count(case when date_part('day',p.created_at - s.first_performance_time) < 30 then 1 else null end) as perf_first_30_days,
                    s.perf_last_30_days, s.join_last_30_days, s.join_list
            from    summary s
                    inner join perf p on p.{selcol} = s.{selcol}
            group by 1, 2, 3, 4, 5, 6, 8, 9, 10
            order by 2 desc
            """
    elif analyticstitle == 'Invite':
        headings = [\
            'Song Name', 'Total Score', 'Invite Score', 'Popularity Score', 'First Performance Score', 'Last Performance Score', \
            '# Performances', '# Partners', '# Invites', '# Joins', 'First Performance', 'Last Performance'\
            ]
        sqlquery = f"""
            select  fixed_title as search_text, total_score, invite_recency_score, popularity_score, first_performance_score,
                    performance_recency_score, num_all_performances, num_partners, num_invites, num_joins,
                    first_performance_time, last_performance_time
            from    my_invite_analysis
            where   fixed_title not in (select item_name from smule_list where list_type = 'EXCLUDE_INVITE_ANALYTICS')
            """
    elif analyticstitle == 'Repeat':
        headings = ['Main Performer', 'Song Name', '# Performances', 'First Performed', 'Last Performed']
        sqlquery = f"""
            select  performers as search_text, fixed_title, count(*) num_performances, min(created_at) as first_performance_time, max(created_at) as last_performance_time
            from    my_performances
            where   created_at between '{fromdate}' and '{todate}'
            and     performers != '{username}'
            group by 1,2
            having count(*) > 1
            order by 3 desc
            """
    elif analyticstitle == 'Favorite Songs':
        headings = ['Song Name', 'Weighted Count', 'First Perf Time', '# Performances', '# Perf - 1 Day', '# Perf - 5 Days', '# Perf - 10 Days', '# Perf - 30 Days']
        sqlquery = f"""
            select  fixed_title as search_text, weighted_cnt, first_performance_time, perf_cnt, perf_1day_cnt, perf_5day_cnt, perf_10day_cnt, perf_30day_cnt
            from    favorite_song
            order by weighted_cnt desc
            """

    #print(sqlquery)
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        analytics.append(d)
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

# Save the performances queried from Smule to the DB
def saveDBFavorites(username,performances):
    i = 0
    # Need to use deepcopy to copy the list of objects so that the original list does not get overwritten
    db_performances = copy.deepcopy(performances)
    # Loop through each performance that has been queried
    for p in db_performances:
        # Use a try block because we want to ignore performances with bad data
        # If any error occurs when processing the performance, simply skip it
        # TODO: Use more granular error checks
        try:
            # Process the PerformanceSinger record for the owner of the performance
            perfFavorite = PerformanceFavorite(\
                        favorited_by_username = username,\
                        performance_key = p['key'],\
                        created_at = p['created_at'],\
                        )
            db.session.merge(perfFavorite)
            # Commit all the changes for the performance if no errors were encountered
            db.session.commit()
            i += 1
        except:
            # If any errors are encountered for the performance, roll back all DB changes made for that performance
            db.session.rollback()
            # Uncomment following line for debugging purposes only
            #raise

    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(performances)} favorites processed"

# Insert/Update data into Singer_Following table
def saveDBSingerFollowing(userFollowing):
    i = 0
    # First, update all rows to set isFollowing to Flase
    db.session.execute("update singer_following set is_following = False, updated_at = now()")
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
