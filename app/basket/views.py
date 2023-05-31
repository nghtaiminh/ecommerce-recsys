from flask import render_template, request, current_app, session, redirect, jsonify, flash, url_for
from flask_login import current_user

from . import basket
from .. import db

from ..models import Product, Interaction, Basket, Order, OrderDetail, Action
from datetime import datetime
from sqlalchemy import text, func, case
from ..recommender import recommend_products


@basket.route("/", methods=["GET"])
def index():
    total_price = 0
    if current_user.is_authenticated:
        # Login -> load basket detail from database
        items = db.session.query(Basket.product_id, Basket.quantity).filter_by(
            user_id=current_user.id
        )
        baskets = {}
        for item in items:
            baskets[str(item.product_id)] = item.quantity
    else:
        baskets = session.get("basket", {})
    products = Product.query.filter(Product.id.in_(baskets.keys()))

    for id, quantity in baskets.items():
        total_price += products.filter(Product.id == id).first().price * quantity

    rec_products = []
    # get add-to-cart items in session
    added = session.get("added", [])
    print("added", added)
    if len(added) > 0:
        added_ids = [id for id, ts in added]
        rec_ids = recommend_products(added_ids)

        whens = {id: index for index, id in enumerate(rec_ids)} 
        sort_logic = case(value=Product.id, whens=whens)

        rec_products = (
            db.session.query(Product)
            .filter(Product.id.in_(list(rec_ids)))
            .order_by(sort_logic)
            .limit(current_app.config["PRODUCT_IN_CAROUSEL"])
        ).all()

    return render_template(
        "basket/index.html",
        recommend_products=rec_products,
        products=products,
        baskets=baskets,
        total_price=total_price,
    )


@basket.route("/add/<id>", methods=["PUT"])
def add(id):
    product = Product.query.filter_by(id=id).first()
    basket_count = 0

    if product is None:
        return jsonify(status=False, message="Product not found")

    # save add-to-cart interaction to session
    added = session.get("added", [])
    action_found = dict(added).get(id, None)
    # if the product is already in the list -> remove it
    if action_found is not None:
        added.pop(added.index((id, action_found)))

    # the add_to_cart action is stored in [oldest, ..., newest]
    added.append((id, datetime.now().timestamp()))

    # limit session views (can set in config.py4)
    limit_session_view = current_app.config["SESSION_VIEWS_LIMIT"]
    if len(added) > limit_session_view:
        added = added[-limit_session_view:]
    session["added"] = added

    if current_user.is_authenticated:
        # authenticated -> save basket detail to database
        add_id = Action.query.filter_by(name="add_to_cart").first().id

        i = Interaction(user=current_user, product=product, action_type_id=add_id)
        db.session.add(i)

        # find the item in basket
        i = Basket.query.filter_by(product_id=id, user_id=current_user.id).first()
        if i is None:
            i = Basket(user=current_user, product=product)
            db.session.add(i)
        else:
            i.quantity = i.quantity + 1
        db.session.commit()
        basket_count = sum(item.quantity for item in current_user.basket)
    else:
        # save to session
        basket = session.get("basket") or {}
        i = basket.get(id, None)
        if i is None:
            basket[id] = 1
        else:
            basket[id] += 1

        session["basket"] = basket
        basket_count = sum(basket.values())

    return jsonify(
        status=True, message="Add to basket successfully", basket_count=basket_count
    )


@basket.route("/remove/<id>", methods=["DELETE"])
def remove(id):
    if current_user.is_authenticated:
        # if user is authenticated -> remove basket details in db
        i = Basket.query.filter_by(product_id=id, user_id=current_user.id).first()
        if i is not None:
            db.session.delete(i)
            db.session.commit()
    else:
        # delete from session
        basket = session.get("basket") or {}
        i = basket.get(id, None)
        if i is not None:
            basket.pop(id)

        session["basket"] = basket
        print(basket)

    # delete add-to-cart interaction from session
    added = session.get("added", [])
    action_found = dict(added).get(id, None)
    if action_found is not None:
        added.pop(added.index((id, action_found)))

    return jsonify(status=True, message="Remove successfully")


@basket.route("/update/<id>", methods=["PUT"])
def update(id):
    data = request.json
    quantity = data.get("quantity", None)

    if quantity is None:
        return jsonify(status=False, message="Quantity not found")

    try:
        quantity = int(quantity)
    except:
        return jsonify(status=False, message="Quantity must be a positive integer")

    # If user is authenticated -> update basket detail in db
    if current_user.is_authenticated:
        i = Basket.query.filter_by(product_id=id, user_id=current_user.id).first()
        if i is not None:
            i.quantity = quantity
            db.session.commit()
    else:
        # update basket detail in session
        basket = session.get("basket") or {}
        i = basket.get(id, None)
        if i is not None:
            basket[id] = quantity
            session["basket"] = basket
            print(basket)

    return jsonify(status=True, message="Update product's quantity successfully")


@basket.route("/checkout", methods=["POST"])
def checkout():
    data = request.form

    name = data.get("name", "")
    email = data.get("email", "")
    address = data.get("address", "")
    user_id = None

    if len(name) < 1 or len(email) < 1 or len(address) < 1:
        flash("Please fill the order information form!")
        return redirect(url_for("basket.index"))

    if current_user.is_authenticated:
        user_id = current_user.id
        name = current_user.name
        email = current_user.email

        items = Basket.query.filter_by(user_id=current_user.id)
        baskets = {}
        for item in items:
            baskets[str(item.product_id)] = item.quantity
        # delete basket detail in db
        items.delete()
        db.session.flush()
    else:
        baskets = session.get("basket", {})
        session["basket"] = {}

    products = Product.query.filter(Product.id.in_(baskets.keys()))

    if len(products.all()) < 1:
        flash("Please choose at least one product")
        db.session.rollback()
        return redirect(url_for("basket.index"))

    # Create order
    order = Order(user_id=user_id, email=email, name=name, address=address)
    db.session.add(order)
    db.session.flush()

    purchase_id = Action.query.filter_by(name="purchase").first().id
    # Create order detail
    for id, quantity in baskets.items():
        p = products.filter(Product.id == id).first()
        detail = OrderDetail(order=order, product=p, quantity=quantity)
        db.session.add(detail)

        # Create interaction
        interaction = Interaction(
            user_id=user_id, product_id=p.id, action_type_id=purchase_id
        )
        db.session.add(interaction)

    db.session.commit()

    return render_template("basket/checkout-successfully.html")
