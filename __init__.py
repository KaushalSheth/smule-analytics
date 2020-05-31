import os

from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_migrate import Migrate
from .smule import fetchSmulePerformances, downloadSong, crawlFavorites
from .db import fetchDBPerformances, saveDBPerformances, saveDBFavorites, fetchDBAnalytics
from datetime import datetime

# Set defaults for global variable that are used in the app
user = None
search_user = None
performances = None
numrows = 200

def update_currtime():
    global currtime
    currtime = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

# Create the app and set up all the routes for the avarious actions that can be taken
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', default='dev'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    from .models import db

    # Prepare app to work with SQLAlchemy and Flask-Migrate
    db.init_app(app)
    migrate = Migrate(app, db)

    # Main home page of the app
    @app.route('/')
    def index():
        update_currtime()
        return render_template('index.html')

    # The search page allows you to search for performances either in the Smule site or the DB
    @app.route('/search', methods=('GET','POST'))
    def search():
        global user, numrows, search_user, startoffset, fromdate, todate, searchtype
        update_currtime()
        # When the form is posted, store the form field values into global variables
        if request.method == 'POST':
            user = request.form['username']
            search_user = user
            numrows = int(request.form['numrows'])
            startoffset = int(request.form['startoffset'])
            fromdate = request.form['fromdate']
            todate = request.form['todate']
            error = None
            searchtype = 'PERFORMANCES'

            if not user:
                error = "Username is required."

            # Depending on which button was clicked, take the appropriate action
            if error is None:
                if request.form['btn'] == 'Search Smule':
                    searchtype = 'PERFORMANCES'
                    return redirect(url_for('query_smule_performances'))
                elif request.form['btn'] == 'Search Favorites':
                    searchtype = 'FAVORITES'
                    return redirect(url_for('query_smule_favorites'))
                elif request.form['btn'] == 'Search Ensembles':
                    searchtype = 'ENSEMBLES'
                    return redirect(url_for('query_smule_ensembles'))
                elif request.form['btn'] == 'Search Invites':
                    searchtype = 'INVITES'
                    return redirect(url_for('query_smule_invites'))
                elif request.form['btn'] == 'Search DB':
                    return redirect(url_for('query_db_performances'))
                else:
                    error = "Invalid selection"

            # If any errors were detected during the post, disaply the erorr message
            flash(error, 'error')

        # When the form is fetched, initialize the global variables and display the search form
        user = None
        performances = None
        return render_template('search.html')

    # This method is referenced in the list_performances HTML page in order to fetch performances for the owner listed
    @app.route('/search_smule_user/<username>')
    def search_smule_user(username):
        global user, searchtype
        user = username
        if searchtype == 'FAVORITES':
            return redirect(url_for('query_smule_favorites'))
        elif searchtype == 'ENSEMBLES':
            return redirect(url_for('query_smule_ensembles'))
        else:
            return redirect(url_for('query_smule_performances'))

    # The Analytics page allows you to choose one of the analytics "reports" you wish to display
    @app.route('/analytics', methods=('GET','POST'))
    def analytics():
        global user, numrows, search_user, startoffset, fromdate, todate, searchtype, analyticslabel
        update_currtime()
        # When the form is posted, store the form field values into global variables
        if request.method == 'POST':
            user = request.form['username']
            fromdate = request.form['fromdate']
            todate = request.form['todate']
            error = None
            searchtype = 'PERFORMANCES'

            if not user:
                error = "Username is required."

            # Depending on which button was clicked, take the appropriate action
            if error is None:
                if request.form['btn'] == 'Title Counts':
                    analyticslabel = "Song Name"
                    return redirect(url_for('query_title_counts'))
                elif request.form['btn'] == 'Partner Counts':
                    analyticslabel = "Partner Username"
                    return redirect(url_for('query_partner_counts'))
                else:
                    error = "Invalid selection"

            # If any errors were detected during the post, disaply the erorr message
            flash(error, 'error')

        # When the form is fetched, initialize the global variables and display the search form
        user = None
        performances = None
        return render_template('analytics_choice.html')

    # This method queries the DB for title analytics using the relevant global variables
    @app.route('/query_title_counts')
    def query_title_counts():
        global user, fromdate, todate, analytics
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        analytics = fetchDBAnalytics("fixed_title",user,fromdate,todate)
        flash(f"{len(analytics)} titles fetched from database")
        return redirect(url_for('analytics_output'))

    # This method queries the DB for partner analytics using the relevant global variables
    @app.route('/query_partner_counts')
    def query_partner_counts():
        global user, fromdate, todate, analytics
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        analytics = fetchDBAnalytics("partner_name",user,fromdate,todate)
        flash(f"{len(analytics)} partners fetched from database")
        return redirect(url_for('analytics_output'))

    # Generic route for displaying performances using global variable
    @app.route('/analytics_output')
    def analytics_output():
        global analytics, user, currtime, analyticslabel

        # This assumes that the performances global variable is set by the time we get here
        return render_template('analytics_output.html', analytics=analytics, user=user, currtime=currtime, analyticslabel=analyticslabel)

    # This method is referenced in the list_performances HTML page in order to fetch performances for the owner listed
    @app.route('/crawl_favorites/<username>')
    def crawl_favorites(username):
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        message = crawlFavorites(username,performances,numrows,startoffset,fromdate,todate)
        flash(message)
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch all performances using global variables set previously
    @app.route('/query_smule_performances')
    def query_smule_performances():
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"performances",fromdate,todate)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch all performances using global variables set previously
    @app.route('/query_smule_invites')
    def query_smule_invites():
        global user, numrows, performances, startoffset, fromdate, todate, invites
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"invites",fromdate,todate)
        flash(f"{len(performances)} invites fetched from Smule")
        return redirect(url_for('list_invites'))

    # This executes the smule function to fetch favorite performances using global variables set previously
    # Luckily for us, the structure of all performances and favorite performances is the same, so we can reuse the objects
    @app.route('/query_smule_favorites')
    def query_smule_favorites():
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"favorites",fromdate,todate)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch favorite ensemble performances using global variables set previously
    # This basically queries all performances but then only includes the ones that are ensembles
    @app.route('/query_smule_ensembles')
    def query_smule_ensembles():
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"ensembles",fromdate,todate)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This method is not currently used - created it just for symmetry - may be removed later if no use is found
    @app.route('/search_db_user/<username>')
    def search_db_user(username):
        global user
        user = username
        return redirect(url_for('query_db_performances'))

    # This executes the db function to fetch performances using global variables set previously
    @app.route('/query_db_performances')
    def query_db_performances():
        global user, numrows, performances, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchDBPerformances(user,numrows,fromdate,todate)
        flash(f"{len(performances)} performances fetched from database")
        return redirect(url_for('list_performances'))

    # Thsi method allows us to take various actions on the list of performances displayed
    @app.route('/submit_performances', methods=('GET','POST'))
    def submit_performances():
        global user, performances
        # We can save the listed performances/favorites to the DB, download them all, or display them on a map (using leaflet)
        if request.form['btn'] == 'Save Performances':
            message = saveDBPerformances(user,performances)
        elif request.form['btn'] == 'Save Favorites':
            message = saveDBFavorites(user,performances)
        elif request.form['btn'] == 'Download All':
            message = download_all_performances()
        elif request.form['btn'] == 'Show Map':
            return render_template('map.html', performances=performances)
        else:
            error = "Invalid source - valid options are 'smule' and 'db'"
        flash(message)
        return redirect(url_for('list_performances'))

    # Generic route for displaying performances using global variable
    @app.route('/list_performances')
    def list_performances():
        global performances, search_user, user
        # This assumes that the performances global variable is set by the time we get here
        return render_template('list_performances.html', performances=performances, search_user=search_user, user=user)

    # Generic route for displaying performances using global variable
    @app.route('/list_invites')
    def list_invites():
        global performances, search_user, user, invites, currtime

        # This assumes that the performances global variable is set by the time we get here
        return render_template('list_invites.html', performances=performances, search_user=search_user, user=user, currtime=currtime)

    # Method to download the performance to local disk
    @app.route('/download_performance/<key>')
    def download_performance(key):
        global performances
        # Look up the performance by key in the global list of performances
        performance = next(item for item in performances if item['key'] == key)
        # Downlod the song to /tmp (hardcoded for now)
        # TODO: Allow specification of download folder as well as add error handling for key not found
        downloadSong(performance["web_url"], "/tmp/" + performance['filename'],performance)
        flash("Successfully downloaded to /tmp/" + performance['filename'])
        return redirect(url_for('list_performances'))

    # Route to downlaod all performances - this could potentially be moved to the smule module
    @app.route('/download_all_performances')
    def download_all_performances():
        global performances
        i = 0
        for performance in performances:
            # Only download joins for ensembles, not the invite itself
            if performance["create_type"] != "invite":
                i += downloadSong(performance["web_url"], "/tmp/" + performance['filename'],performance)
        retVal = f"Successfully downloaded {i} songs to /tmp"
        print(retVal)
        return retVal

    return app
