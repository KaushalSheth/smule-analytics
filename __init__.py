import os

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_migrate import Migrate

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
            username = request.form['username']
            error = None

            if not username:
                error = "Username is required."

            if error is None:
                return redirect(url_for('list_performances'))

            flash(error, 'error')

        return render_template('search.html')

    return app

