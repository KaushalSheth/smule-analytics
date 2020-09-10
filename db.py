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

# Method to query performances for a user
def fetchDBPerformances(username,maxperf=9999,fromdate="2018-01-01",todate="2030-01-01"):
    global performances
    performances = []
    i = 0

    # Build appropriate query - if username = 'KaushalSheth1', then don't apply any filters
    if username == 'KaushalSheth1':
        sqlquery = "select * from my_performances where created_at between '" + fromdate + "' and '" + todate + "'"
    else:
        sqlquery = "select * from my_performances where created_at between '" + fromdate + "' and '" + todate + "' and owner_handle = '" + username + "'"
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
        title = fix_title(performance['title'])
        performers = filename_parts[1]
        filename = f"{title} - {performers}"
        performances[i]['filename'] = filename
        i += 1

    return performances

# Method to query title and partner analytics for a user
def fetchDBAnalytics(groupbycolumn,username,fromdate="2018-01-01",todate="2030-01-01"):
    global analytics
    analytics = []
    if groupbycolumn == "partner_name":
        othercolumn = "fixed_title"
    else:
        othercolumn = "partner_name"

    # Build appropriate query
    # Start with the base query
    sqlquery = f"""
        select  case when {groupbycolumn} != '{username}' then {groupbycolumn} else owner_handle end as group_by_column,
                count(*) as count_all_time,
                count(case when created_at > (now() - '30 days'::interval day) then 1 else null end) as count_30_days,
                count(case when created_at > (now() - '90 days'::interval day) then 1 else null end) as count_90_days,
                count(case when created_at > (now() - '180 days'::interval day) then 1 else null end) as count_180_days,
                count(case when created_at <= (now() - '180 days'::interval day) then 1 else null end) as count_older,
                string_agg(distinct case when {othercolumn} != '{username}' then {othercolumn} else owner_handle end,', ') as join_list
        from all_performances
        where created_at between '{fromdate}' and '{todate}'
        and (owner_handle = '{username}' or partner_name = '{username}')
        """
    # Append GROUP BY/ORDER BY clause
    sqlquery += " group by 1 order by 4 desc, 2 desc"

    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        # Add the keys to the dict that are not saved to the DB but used for other processing
        analytics.append(d)

    return analytics

# Method to query longevity analytics
def fethLongevityAnalytics(username,fromdate="2018-01-01",todate="2030-01-01"):
    global analytics
    analytics = []
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
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        # Add the keys to the dict that are not saved to the DB but used for other processing
        analytics.append(d)

    return analytics

# Method to query invite analytics
def fetchInviteAnalytics(username,fromdate="2018-01-01",todate="2030-01-01"):
    global analytics
    analytics = []
    sqlquery = f"select * from my_invite_analysis where fixed_title not in (select fixed_title from song_list where list_type = 'EXCLUDE_INVITE_ANALYTICS')"
    # Execute the query and build the analytics list
    result = db.session.execute(sqlquery)
    for r in result:
        # Convert the result row into a dict we can add to performances
        d = dict(r.items())
        # Add the keys to the dict that are not saved to the DB but used for other processing
        analytics.append(d)

    return analytics

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
