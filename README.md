# smule-analytics
I started this project with the intention to fetch my Smule data and store it in a local DB for doing analytics such as who are the people with whom I have performed the most number of duets, which of my songs have the most Loves, where are the people I have performed with located, etc.  I do still plan to implement these features, but I started out with a feature I wish existed in the Smule site, which is to list my (or any user's) performances in a simple format that allows me to listen to them and download them.

I developed the project in a pipenv Python 3.7 environment with Flask.  The backend DB is a PostgreSQL database running in a Docker container I downloaded from Docker Hub.  Below are the instructions for setting up the dev environment - The examples are for Mac since that is my environment.  In the future, I will look into packaging the code in an easier to install package, but that is a lower priority.

UPDATE: I have finally implemented the mapping feature using [Leaflet](https://leafletjs.com/reference-1.5.0.html#marker) and [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster).  When you get to the list of performances by either querying from the DB or form Smule, you simply click the "Show Map" button to disaply a map with pins for each of the performances.  If there are multiple performances in the same location, they are clustered together when you zoon out and shown as individual pins as you zoom in.  No installation is needed for this - I simply link to the appropriate stylesheets and Javascript in my HTML code.


**Install Docker**
* Install Docker for Mac: https://docs.docker.com/docker-for-mac/install/

**Run PostgreSQL using a single Docker command**

```docker run --name my_postgres -p 5432:5432 -e POSTGRES_PASSWORD=password -v /c/00data/postgres/data:/var/lib/postgresql/data -d postgres:11```
```OBSOLETE: docker run -d --name my_postgres -v my_dbdata:/var/lib/postgresql/data -p 5432:5432 postgres:11```

**Confirm that PostgreSQL is running**

```docker logs -f my_postgres```

**Create the database and user, and grant privileges**

```
docker exec -it my_postgres psql -U postgres -c "create database smule_db"

docker exec -it my_postgres psql -U postgres -c "create user smule password 'smule123'"

docker exec -it my_postgres psql -U postgres -c "grant all privileges on database smule_db to smule"
```

**Clone this repository**

```
git clone https://github.com/KaushalSheth/smule-analytics.git
```

**Create .env file with DB connection info**

```
export DB_USERNAME='smule'
export DB_PASSWORD='smule123'
export DB_HOST='localhost'
export DB_PORT='5432'
export DB_NAME='smule_db'
export FLASK_ENV='development'
export FLASK_APP='.'
```

**Install pipenv if not already instaled**

```brew install pipenv```

**Setup pipenv environment from git base folder that contains Pipfile and start shell**

```
export LIBRARY_PATH=/usr/local/Cellar/openssl/1.0.2r/lib
pipenv install
pipenv shell
```
Note: On my Mac at least, I had an issue installing psycopg2, and the workaround that worked for me was to set the LIBRARY_PATH listed above.  Your mileage might vary

**Upgrade your DB using commands in the repository - assumes above PostgreSQL steps were completed**

```flask db upgrade```

**Run the Flask app**

```flask run --host=0.0.0.0 --port=3000```

**Access your app in your browser using the below URL**

```http://localhost:3000/search```



