import os

# Fetch configs from env variables, or set to default values if env variable not set
db_host = os.environ.get('DB_HOST', default='localhost')
db_port = os.environ.get('DB_PORT', default='5432')
db_name = os.environ.get('DB_NAME', default='smule_db')
db_user = os.environ.get('DB_USERNAME', default='smule')
db_password = os.environ.get('DB_PASSWORD', default='smule123')

# Set up the database URI for SQLAlchemy, along with values for certain options
SQLALCHEMY_DATABASE_URI = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
