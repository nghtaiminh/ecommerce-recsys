import os
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "demo online bookstore"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Config for flask-sessions
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = "filesystem"

    PRODUCT_PER_PAGE = 24
    PRODUCT_IN_CAROUSEL = 12
    SESSION_VIEWS_LIMIT = 40

    CATEGORY_BANNERS = 8
    CATEGORY_FILTER_LIMIT = 10

    # ORDER_PER_PAGE = 5

    INTERACTION_PER_PAGE = 20

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    os.environ["DEBUG"] = "1"
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "postgresql://postgres:123456@localhost:5432/bookstore"
    )

    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    if not database_exists(engine.url):
        create_database(engine.url)



config = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
}
