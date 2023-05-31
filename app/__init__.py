from config import config
from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

bootstrap = Bootstrap4()
db = SQLAlchemy()

# FLASK-SESSIONS
session = Session()

# LoginManager
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    session.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .basket import basket as basket_blueprint
    app.register_blueprint(basket_blueprint, url_prefix="/basket")

    return app
