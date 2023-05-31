from flask import Blueprint

basket = Blueprint("basket", __name__)

from . import views
