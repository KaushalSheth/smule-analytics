from .models import db, Performance, Singer, PerformanceSinger, PerformanceFavorite
from .utils import fix_title
from sqlalchemy import text
import copy

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
        d['performers'] = ""
        d['pic_filename'] = ""
        d['fixed_title'] = ""
        d['partner_name'] = ""
        d['create_type'] = ""
        d['perf_status'] = ""
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
            del p['performers']
            del p['pic_filename']
            del p['fixed_title']
            del p['partner_name']
            del p['display_handle']
            del p['display_pic_url']
            del p['create_type']
            del p['perf_status']

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
