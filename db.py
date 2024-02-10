from .models import db, Performance, Singer, PerformanceSinger, PerformanceFavorite, TitleMapping, SingerFollowing, GeoCache, TitleMetadata
from .constants import *
from .utils import fix_title,build_comment
from sqlalchemy import text, Table, Column
import copy

# Method to execute specified query and return result as a list of rows
def execDBQuery(sqlquery):
    results = []
    # Some queries (like updates) don't return any results, so catch and ignore those errors
    try:
        result = db.session.execute(text(sqlquery))
        for r in result:
            # Convert the result row into a dict we can add to performances
            d = r._asdict()
            results.append(d)
    except Exception as e:
        # If an exception happened, we likely executed an INSERT or UPDATE, so commit it
        db.session.commit()
        print(e)
    return results

# Method to feth Title Mappings
def fetchDBTitleMappings():
    global titleMappings
    titleMappings = dict()
    result = db.session.execute(text("select smule_title,mapped_title from title_mapping order by length(smule_title) desc"))
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
    result = db.session.execute(text(query))
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
    result = db.session.execute(text('truncate table title_mapping'))
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
    fixCount = db.session.execute(text(updateSQL)).rowcount
    print(f"Rows updated = {fixCount}")
    db.session.commit()

    return fixCount

# Method to query performers
def fetchDBPerformers(fromdate="2018-01-01",todate="2030-01-01"):
    performers = []
    sqlquery = f"""
        select * from (
            select  p.performers, coalesce(p.display_pic_url,s.pic_url) as display_pic_url,
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
        order by partner_stats desc, joiner_stats desc
        """
    # Execute the query and build the performers list
    performers = execDBQuery(sqlquery)
    return performers

# Method to query performers
def fetchDBPerformerMapInfo(utilitiesOptions):
    distance = utilitiesOptions['distance']
    dayssincelastperf = utilitiesOptions['dayssincelastperf']
    centlat = utilitiesOptions['centlat']
    centlon = utilitiesOptions['centlon']
    performerMapInfo = []
    sqlquery = f"""
        select  'performers' as create_type, last_perf_time as fixed_title, lat as owner_lat, lon as owner_lon, pic_url as display_pic_url, performed_by as display_handle, city as orig_track_city
        from    singer_location
        where   calculate_distance({centlat},{centlon},lat,lon,'M') <= {distance}
        and     last_perf_time > current_timestamp - interval '{dayssincelastperf} days'
        --and     not( smule_hq_ind )
        """
    # Execute the query and build the performers list
    performerMapInfo = execDBQuery(sqlquery)
    return performerMapInfo

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
        	-- Look at the last N months ending last month
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
        select 	pr.*, s.pic_url, to_char(perf_month,'Mon YYYY') as perf_month_str,
        		row_number() over(partition by monthly_rank order by perf_month) as col_nbr
        from 	perf_ranked pr
        		inner join singer s on s.account_id = pr.owner_account_id
        where 	monthly_rank <= 10
        order by monthly_rank, perf_month desc;
        """
    # Execute the query and build the performers list
    performers = execDBQuery(sqlquery)
    return performers

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
        with
            myself as (
                select  'KaushalSheth1' as handle
            ),
            perf_stats as (
                select  s.performed_by,
                        max(p.created_at) as last_performance_time,
                        max(case when p.owner_handle = m.handle then p.created_at else null end) as last_join_time,
                        count(case when p.created_at > current_timestamp - interval '30 days' then p.performers else null end) as recent_perf_cnt,
                        count(case when p.owner_handle = m.handle then p.performers else null end) as join_cnt,
                        count(case when p.owner_handle = m.handle and p.created_at > current_timestamp - interval '30 days' then 1 else null end) as recent_join_cnt
                from    singer s cross join myself m
                        left outer join performance p on p.performers = s.performed_by
                group by 1
            )
        select  p.*, coalesce(js.recent_perf_cnt,0) as recent_perf_cnt, coalesce(js.join_cnt,0) as join_cnt, coalesce(js.recent_join_cnt,0) as recent_join_cnt, js.last_performance_time, js.last_join_time
        from    all_performances p
                left outer join perf_stats js on js.performed_by = p.partner_name
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
    #print(sqlquery)
    # Check the PerformanceSinger table for existence of the singer on the performance
    result = db.session.execute(text(sqlquery))
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
        joinCount = d['join_cnt']
        recentJoinCount = d['recent_join_cnt']
        recentPerfCount = d['recent_perf_cnt']
        # Set display handle and pic_url based on user we are searching for
        if d['owner_handle'] == username:
            d['display_handle'] = d['partner_name']
            #d['display_pic_url'] = d['partner_pic_url']
            # Construct comment for joiner
            d['comment'] = build_comment('@' + d['display_handle'] + ' thanks for joining...')
        else:
            d['display_handle'] = d['owner_handle']
            d['comment'] = build_comment('@' + d['display_handle'])
        d['join_cnt'] = f"{joinCount}|{recentJoinCount}"
        performances.append(d)
        i += 1
        if i >= maxperf:
            break

    return performances

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
            #del p['display_pic_url']
            del p['create_type']
            del p['joiners']
            del p['recording_url']
            del p['comment']
            del p['yt_search']
            del p['web_url_full']
            del p['rating_nbr']
            del p['join_cnt']
            del p['recent_join_cnt']
            del p['last_performance_time']
            del p['last_join_time']

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
    # Update parent_key column for joins to the most recent invite
    updateParentKeys()
    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(performances)} performances processed"
# Update parent_key for joins
def updateParentKeys():
    sqlquery = """
        update performance
        set parent_key = i.invite_key
        from (
        with
        joins as (select * from my_performances where join_ind = 1),
        invites as (select * from my_performances where invite_ind = 1),
        ji as (
        	select 	j.key as join_key, j.fixed_title, j.created_at as join_created_at, j.performers,
        			i.created_at as invite_created_at, i.key as invite_key
        	from 	joins j
        			inner join invites i on i.fixed_title = j.fixed_title and i.created_at <= j.created_at
        	),
        dups as (
        	select 	join_key, fixed_title, join_created_at, performers,
        			first_value(invite_created_at) over w as invite_created_at,
        			first_value(invite_key) over w as invite_key
        	from 	ji
        	window w as (partition by join_key order by invite_created_at desc)
        	)
        select distinct join_key, invite_key from dups
        ) i
        where performer_handles like '%KaushalSheth1%'
        and key = i.join_key
        and parent_key is null
        """
    execDBQuery(sqlquery)
    return 0
# SAve title metadata to DB
def saveDBTitleMetadata(titleMetadataList):
    i = 0
    # Loop through and merge tiutle metadata
    for tm in titleMetadataList:
        try:
            # Convert the title metadata record to the titleMetadata class for SQLAlchemy and merge with the title_metadata queried from DB
            ntm = TitleMetadata(**tm)
            db.session.merge(ntm)
            db.session.commit()
            i += 1
        except:
            db.session.rollback()
            raise
    return f"{i} out of {len(titleMetadataList)} title metadata processed"

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

def fetchDBUserFollowing():
    rs = execDBQuery("select account_id from singer_following where is_following")
    followingAccountIds = []
    for r in rs:
        followingAccountIds.append(r['account_id'])
    return followingAccountIds

# Insert/Update data into Singer_Following table
def saveDBSingerFollowing(userFollowing):
    i = 0
    # Loop through and insert/update all the rows
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

    # Return a message indicating how many rows were successfully processed out of the total
    return f"{i} out of {len(userFollowing)} SingerFollowing processed"
