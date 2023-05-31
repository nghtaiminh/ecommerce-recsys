from datetime import datetime

from flask import Blueprint, session
from flask_login import current_user
from ..recommender import recommenders

main = Blueprint("main", __name__)


@main.app_context_processor
def inject_now():
    return {"now": datetime.utcnow()}


@main.app_context_processor
def inject_recommenders():
    return {"recommenders": recommenders}


@main.app_context_processor
def inject_basket_count():
    basket_count = 0
    if current_user.is_authenticated:
        basket_count = sum(item.quantity for item in current_user.basket)
    else:
        basket_count = sum(session.get("basket", {}).values())

    return {"basket_count": basket_count}


@main.app_template_filter()
def category_in(c, string):
    items = string.replace(" ", "").split(",")
    return str(c) in items


@main.app_template_filter()
def remove_category(string, c):
    items = string.replace(" ", "").split(",")
    items.remove(str(c))
    return ",".join(items)


from . import views
