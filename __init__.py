import os

from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_migrate import Migrate
from .smule import fetchPerformances

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
        if request.method == 'POST':
            g.user = request.form['username']
            error = None

            if not g.user:
                error = "Username is required."

            if error is None:
                return redirect(url_for('query_performances'))

            flash(error, 'error')

        g.user = None
        return render_template('search.html')

    @app.route('/query_performances')
    def query_performances():
        #g.performances = fetchPerformances(g.user,25)
        g.performances = fetchPerformances("KaushalSheth1",25)
        return redirect(url_for('list_performances'))

    @app.route('/list_performances')
    def list_performances():
        #return render_template('list_performances.html', performances=g.performances)
        return render_template('list_performances.html', performances=fetchPerformances("yaak_sumney",25))

    return app

