from .models import db, Performance, Singer, PerformanceSinger

# Method to query performances for a user
def fetchDBPerformances(username,maxperf=9999):
    global performances

    # Check the PerformanceSinger table for existence of the singer on the performance
    performances = db.session.query(Performance).\
            join(PerformanceSinger).\
            join(Singer).\
            filter_by(performed_by = username).all()
    return performances

# Save the performances queried from Smule to the DB
def saveDBPerformances(performances):
    # TODO: Optimize to not query all data from DB, but only a subset that is relevant
    singers = db.session.query(Singer).all()
    db_performances = db.session.query(Performance).all()
    db_perfsingers = db.session.query(PerformanceSinger).all()

    i = 0
    # Loop through each performance that has been queried
    for p in performances:
        # Use a try block because we want to ignore performances with bad data
        # If any error occurs when processing the performance, simply skip it
        # TODO: Use more granular error checks
        try:
            # The other_performers list is not part of the Performance class, so extract it to a variable and delete from the record
            other_performers = p['other_performers']
            del p['other_performers']

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

            # Convert the performance record to the Performance class for SQLAlchemy and merge with the perfroamnces queried from DB
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

    # Return a message indicating how many performances were successfully processed out of the total
    return f"{i} out of {len(performances)} performances processed"
