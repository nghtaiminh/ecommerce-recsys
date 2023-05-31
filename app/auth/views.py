from flask import current_app, flash, redirect, request, url_for, session
from flask_login import current_user, login_required, login_user, logout_user
from datetime import datetime
from .. import db
from ..models import User, Interaction, Basket, Action
from . import auth
from .forms import LoginForm, RegistrationForm


def add_data(user: User):
    # Login -> transfer interaction data from session to database for the user
    basket = session.get("basket", {})
    if len(basket) > 0:
        # update the quantity of the basket
        for id, quantity in basket.items():
            i = Basket(user=user, product_id=id, quantity=quantity)
            db.session.add(i)
            try:
                db.session.commit()
            except:
                db.session.rollback()

    views = session.get("viewed", [])
    if len(views) > 0:
        # transfer the view interaction from session to database
        view_id = Action.query.filter_by(name="view").first().id
        for (id, ts) in views:
            i = Interaction(
                user=user,
                product_id=id,
                action_type_id=view_id,
                timestamp=datetime.fromtimestamp(ts),
            )
            db.session.add(i)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                
    added = session.get("added", [])
    if len(added) > 0:
        # transfer the add_to_cart interaction from session to database
        add_to_cart_id = Action.query.filter_by(name="add_to_cart").first().id
        for (id, ts) in added:
            i = Interaction(
                user=user,
                product_id=id,
                action_type_id=add_to_cart_id,
                timestamp=datetime.fromtimestamp(ts),
            )
            db.session.add(i)
            try:
                db.session.commit()
            except:
                db.session.rollback()

    session["basket"] = {}




@auth.route("/login", methods=["POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            add_data(user)
        else:
            flash("Invalid username or password.")
    else:
        for error in form.errors:
            flash(form.errors[error][0])

    next = request.args.get("next")
    if next is None or not next.startswith("/"):
        next = url_for("main.index")
    return redirect(next)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@auth.route("/register", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=form.password.data,
            email=form.email.data,
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        add_data(user)
        flash("You have been registered and logged in.")
    else:
        for error in form.errors:
            flash(form.errors[error][0])

    next = request.args.get("next")
    if next is None or not next.startswith("/"):
        next = url_for("main.index")
    return redirect(next)
