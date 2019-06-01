from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Performance(db.Model):
    key = db.Column(db.String(30), primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.Datetime, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=True)
    ensemble_type = db.Column(db.String(10), nullable=True)
    child_count = db.Column(db.Integer, nullable=True)
    app_uid = db.Column(db.String(20), nullable=True)
    arr_key = db.Column(db.String(30), nullable=True)
    orig_track_city = db.Column(db.String(40), nullable=True)
    orig_track_country = db.Column(db.String(40), nullable=True)
    media_url = db.Column(db.String(200), nullable=True)
    video_media_url = db.Column(db.String(200), nullable=True)
    video_media_mp4_url = db.Column(db.String(200), nullable=True)
    web_url = db.Column(db.String(200), nullable=True)
    cover_url = db.Column(db.String(100), nullable=True)
    total_performers = db.Column(db.Integer, nullable=True)
    total_listens = db.Column(db.Integer, nullable=True)
    total_loves = db.Column(db.Integer, nullable=True)
    total_comments = db.Column(db.Integer, nullable=True)
    total_commenters = db.Column(db.Integer, nullable=True)
    performed_by = db.Column(db.String(50), nullable=True)
    performed_by_url = db.Column(db.String(50), nullable=True)
    owner_account_id = db.Column(db.Integer, db.ForeignKey('singer.account_id'), nullable=False)
    owner_lat = db.Column(db.Float, nullable=True)
    owner_lon = db.Column(db.Float, nullable=True)

class Singer(db.Model):
    account_id = db.Column(db.Integer, primary_key=True)
    performed_by = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(50), nullable=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    pic_url = db.Column(db.String(200), nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    is_vip = db.Column(db.Boolean, nullable=True)
    is_verified = db.Column(db.Boolean, nullable=True)

class PerformanceSinger(db.Model):
    performance_key = db.Column(db.Integer, db.ForeignKey('performance.key'), primary_key=True)
    singer_account_id = db.Column(db.Integer, db.ForeignKey('singer.account_id'), primary_key=True)

