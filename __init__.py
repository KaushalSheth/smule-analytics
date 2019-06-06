import os

from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_migrate import Migrate
from .smule import fetchSmulePerformances, downloadSong
from .db import fetchDBPerformances, saveDBPerformances
user = None
performances = None
numrows = 200

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

    db.init_app(app)
    migrate = Migrate(app, db)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/search', methods=('GET','POST'))
    def search():
        global user, numrows
        if request.method == 'POST':
            user = request.form['username']
            numrows = int(request.form['numrows'])
            error = None

            if not user:
                error = "Username is required."

            if error is None:
                if request.form['btn'] == 'Search Smule':
                    return redirect(url_for('query_smule_performances'))
                elif request.form['btn'] == 'Search DB':
                    return redirect(url_for('query_db_performances'))
                else:
                    error = "Invalid source - valid options are 'smule' and 'db'"

            flash(error, 'error')

        user = None
        return render_template('search.html')

    @app.route('/search_smule_user/<username>')
    def search_smule_user(username):
        global user
        user = username
        return redirect(url_for('query_smule_performances'))

    @app.route('/query_smule_performances')
    def query_smule_performances():
        global user, numrows, performances
        performances = fetchSmulePerformances(user,numrows)
        return redirect(url_for('list_performances'))

    @app.route('/search_db_user/<username>')
    def search_db_user(username):
        global user
        user = username
        return redirect(url_for('query_db_performances'))

    @app.route('/query_db_performances')
    def query_db_performances():
        global user, numrows, performances
        performances = fetchDBPerformances(user,numrows)
        return redirect(url_for('list_performances'))

    @app.route('/save_db_performances', methods=('GET','POST'))
    def save_db_performances():
        global performances
        singers = saveDBPerformances(performances)
        flash(f"{len(singers)} singers added")
        return redirect(url_for('list_performances'))

    @app.route('/list_performances')
    def list_performances():
        global performances
        return render_template('list_performances.html', performances=performances)

    @app.route('/download_performance/<key>')
    def download_performance(key):
        global performances
        performance = next(item for item in performances if item['key'] == key)
        downloadSong(performance["web_url"], "/tmp/" + performance["filename"])
        return redirect(url_for('list_performances'))

    return app

