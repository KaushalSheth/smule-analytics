from .models import db, Performance, Singer, PerformanceSinger

def fetchDBPerformances(username,maxperf=9999):
    global performances

    performances = db.session.query(Performance).filter_by(owner_handle = username).all()
    return performances

def saveDBPerformances(performances):
    singers = db.session.query(Singer).all()
    db_performances = db.session.query(Performance).all()

    for p in performances:
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

    db.session.commit()

    return singers
