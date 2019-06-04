from .models import db, Performance, Singer, PerformanceSinger

def fetchDBPerformances(username,maxperf=9999):
    global performances

    performances = []
    #performances = db.session.query(Performance).filter_by(performed_by == username).all()
    #performances = db.session.query(Performance).all()
    return performances
