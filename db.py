from .models import db, Performance, Singer, PerformanceSinger

def fetchDBPerformances(username,maxperf=9999):
    global performances

    performances = db.session.query(Performance).\
            join(PerformanceSinger).\
            join(Singer).\
            filter_by(performed_by = username).all()
    return performances

def saveDBPerformances(performances):
    singers = db.session.query(Singer).all()
    db_performances = db.session.query(Performance).all()
    db_perfsingers = db.session.query(PerformanceSinger).all()

    for p in performances:
        other_performers = p['other_performers']
        del p['other_performers']
        singer = Singer(\
                    account_id = p['owner_account_id'],\
                    performed_by = p['owner_handle'],\
                    pic_url = p['owner_pic_url'],\
                    lat = p['owner_lat'],\
                    lon = p['owner_lon']\
                    )
        db.session.merge(singer)
        np = Performance(**p)
        db.session.merge(np)
        perfSinger = PerformanceSinger(\
                    performance_key = p['key'],\
                    singer_account_id = p['owner_account_id']\
                    )
        db.session.merge(perfSinger)
        for o in other_performers:
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

    db.session.commit()

    return f"{len(performances)} performances processed"
