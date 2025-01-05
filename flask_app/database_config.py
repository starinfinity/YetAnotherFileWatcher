import os

from flask import Flask
from flask_app.models import db


def setup_app():
    template_dir = os.path.abspath('./flask_app/templates')
    app = Flask(__name__, template_folder=template_dir)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, '../instance/scheduler.db')  # Adjust for instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app
