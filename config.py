import os

db_host = os.environ.get('DB_HOST', default='localhost')
db_port = os.environ.get('DB_PORT', default='5432')
db_name = os.environ.get('DB_NAME', default='smule')
db_user = os.environ.get('DB_USERNAME', default='ksheth')
db_password = os.environ.get('DB_PASSWORD', default='smule123')

SQLALCHEMY_DATABASE_URI = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
