from .models import db, Performance, Singer, PerformanceSinger, PerformanceFavorite, TitleMapping
from .utils import fix_title
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

# Method to query performances for a user
def fetchDBPerformancesOrig(username,maxperf=9999):
    global performances

    # Check the PerformanceSinger table for existence of the singer on the performance
    performances = db.session.query(Performance).\
            join(PerformanceSinger).\
            join(Singer).\
            filter_by(performed_by = username).all()

    return performances

# Method to query performers
def fetchDBPerformers(fromdate="2018-01-01",todate="2030-01-01"):
    performers = []
    sqlquery = f"""
        select  p.performers, s.pic_url as display_pic_url,
                lpad(count(*)::varchar,3,'0') || '-' || p.performers as display_handle,
                max(p.created_at) as last_performance_time
        from    my_performances p
                inner join singer s on s.performed_by = p.performers
        where   p.created_at between '{fromdate}' and '{todate}'
        group by 1, 2
        order by 4 desc
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
def fetchDBPerformances(username,maxperf=9999,fromdate="2018-01-01",todate="2030-01-01",titleMappings=[]):
    global performances
    performances = []
    i = 0

    # Build appropriate query - if username = 'KaushalSheth1', then don't apply any filters
    if username == 'KaushalSheth1':
        sqlquery = "select * from my_performances where created_at between '" + fromdate + "' and '" + todate + "'"
    else:
        sqlquery = f"""
            select  p.*
            from    all_performances p
            where   p.created_at between '{fromdate}' and '{todate}'
            and     exists (
                        select  1
                        from    performance_singer ps
                                inner join singer s on s.account_id = ps.singer_account_id and performed_by = '{username}'
                        where   ps.performance_key = p.key
                        )
            """
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
        d['partner_name'] = ""
        d['create_type'] = ""
        d['joiners'] = ""
        # TODO: Need to figure out how to get the partner handle and pic_URL here
        d['display_handle'] = d['owner_handle']
        d['display_pic_url'] = d['owner_pic_url']
        performances.append(d)
        i += 1
        if i >= maxperf:
            break

    i = 0
    for performance in performances:
        filename_parts = performance['filename'].split(' - ')
        #title = fix_title(filename_parts[0])
        title = fix_title(performance['title'],titleMappings)
        performers = filename_parts[1]
        filename = f"{title} - {performers}"
        performances[i]['filename'] = filename
        i += 1

    return performances

# Method to query title and partner analytics for a user
def fetchDBAnalytics(analyticstitle,username,fromdate="2018-01-01",todate="2030-01-01"):
    global analytics, headings
    analytics = []
    headings = []
    # Build appropriate query based on analytics title passed in.  Set headings accordingly
    if analyticstitle in ['Partner Count','Title Count']:
        if analyticstitle == 'Partner Count':
            headings = ['Partner','All-Time Count','Last 30 Days','Last 90 Days','Last 180 Days','Older Than 180 Days','Join List']
            selcol = "performers"
            listcol = "fixed_title"
        else:
            headings = ['Song Name','All-Time Count','Last 30 Days','Last 90 Days','Last 180 Days','Older Than 180 Days','Join List']
            selcol = "fixed_title"
            listcol = "performers"
        joinClause = f"""
            inner join (
                select {selcol},{listcol},lpad(count(*)::varchar,2,'0') || '-' || {listcol} as list_col, count(*) as num_performances
                from my_performances
                group by 1,2
                ) grp on grp.{selcol} = p.{selcol} and grp.{listcol} = p.{listcol}
                """
        # Build appropriate query
        # Start with the base query
        sqlquery = f"""
            select  grp.{selcol} as group_by_column,
                    count(*) as count_all_time,
                    count(case when created_at > (now() - '30 days'::interval day) then 1 else null end) as count_30_days,
                    count(case when created_at > (now() - '90 days'::interval day) then 1 else null end) as count_90_days,
                    count(case when created_at > (now() - '180 days'::interval day) then 1 else null end) as count_180_days,
                    count(case when created_at <= (now() - '180 days'::interval day) then 1 else null end) as count_older,
                    string_agg(distinct grp.list_col,', 'order by grp.list_col desc) as join_list
            from my_performances p {joinClause}
            where p.created_at between '{fromdate}' and '{todate}'
            """
        # Append GROUP BY/ORDER BY clause
        sqlquery += " group by 1 order by 4 desc, 2 desc"
    elif analyticstitle == 'Longevity':
        headings = ['Song Name', 'All-Time Count', 'First Performed', 'Last Performed', 'Longevity', 'Partner Count', 'Partner List']
        sqlquery = f"""
            select  fixed_title,
                    count(*) as count_all_time,
                    min(created_at) as first_date,
                    max(created_at) as last_date,
                    date_part('day',max(created_at)-min(created_at)) as longevity,
                    count(distinct case when partner_name != '{username}' then partner_name else owner_handle end) as num_partners,
                    string_agg(distinct case when partner_name != '{username}' then partner_name else owner_handle end,', ') as join_list
            from all_performances
            where created_at between '{fromdate}' and '{todate}'
            and (owner_handle = '{username}' or partner_name = '{username}')
            group by 1 order by 4,3 desc
            """
    elif analyticstitle == 'Invite':
        headings = [\
            'Song Name', 'Total Score', 'Invite Score', 'Popularity Score', 'First Performance Score', 'Last Performance Score', \
            '# Performances', '# Partners', '# Invites', '# Joins', 'First Performance', 'Last Performance'\
            ]
        sqlquery = f"""
            select  fixed_title, total_score, invite_recency_score, popularity_score, first_performance_score,
                    performance_recency_score, num_all_performances, num_partners, num_invites, num_joins,
                    first_performance_time, last_performance_time
            from    my_invite_analysis
            where   fixed_title not in (select fixed_title from song_list where list_type = 'EXCLUDE_INVITE_ANALYTICS')
            """
    elif analyticstitle == 'Repeat':
        headings = ['Main Performer', 'Song Name', '# Performances', 'First Performed', 'Last Performed']
        sqlquery = f"""
            select  performers as main_performer, fixed_title, count(*) num_performances, min(created_at) as first_performance_time, max(created_at) as last_performance_time
            from    my_performances
            where   created_at between '{fromdate}' and '{todate}'
            and     performers != '{username}'
            group by 1,2
            having count(*) > 1
            order by 3 desc
            """
    elif analyticstitle == "First Performance":
        headings = ['Song Name','First Performance Month','First Partner','# Performances',\
            '1 Day','5 Day','10 Day','30 Day','60 Day','90 Day',\
            'First Performance Time','LastPerformance Time'\
            ]
        sqlquery = f"""
            with
            perf_stats as (
                select  fixed_title,
                        first_value(created_at) over w_ord as first_performance_time,
                        first_value(performers) over w_ord as first_partner,
                        row_number() over w_ord as rn,
                        count(1) over w_all as num_performances_total,
                        max(created_at) over w_all as last_performance_time
                from    my_performances
                window  w_ord as (partition by fixed_title order by created_at), w_all as (partition by fixed_title)
                ),
            first_perf as (select *, to_char(first_performance_time,'YYYY-MM') as first_performance_month from perf_stats where rn = 1),
            title_stats as (
                select  mp.fixed_title,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 1 then 1 else null end) as num_performances_1_day,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 5 then 1 else null end) as num_performances_5_day,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 10 then 1 else null end) as num_performances_10_day,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 30 then 1 else null end) as num_performances_30_day,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 60 then 1 else null end) as num_performances_60_day,
                        count(case when date_part('day',mp.created_at - fp.first_performance_time) < 90 then 1 else null end) as num_performances_90_day
                from    my_performances mp
                        inner join first_perf fp on fp.fixed_title = mp.fixed_title
                group by 1
                )
            select  fp.fixed_title, fp.first_performance_month, fp.first_partner, fp.num_performances_total,
                    ts.num_performances_1_day,ts.num_performances_5_day,ts.num_performances_10_day,
                    ts.num_performances_30_day,ts.num_performances_60_day,ts.num_performances_90_day,
                    fp.first_performance_time, fp.last_performance_time
            from    first_perf fp
                    inner join title_stats ts on ts.fixed_title = fp.fixed_title
            where   first_performance_time between '{fromdate}' and '{todate}'
            """

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
            #raise

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
