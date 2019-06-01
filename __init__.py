import os

from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_migrate import Migrate
from .smule import fetchPerformances
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
        return 'Index'

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
                return redirect(url_for('query_performances'))

            flash(error, 'error')

        user = None
        return render_template('search.html')

    @app.route('/search_user/<username>')
    def search_user(username):
        global user
        user = username
        return redirect(url_for('query_performances'))

    @app.route('/query_performances')
    def query_performances():
        global user, numrows, performances
        performances = fetchPerformances(user,numrows)
        return redirect(url_for('list_performances'))

    @app.route('/list_performances')
    def list_performances():
        global performances
        return render_template('list_performances.html', performances=performances)

    return app

