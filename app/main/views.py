from flask import render_template, request, current_app, session, redirect, url_for,abort
from flask_login import current_user
from . import main
from .. import db
from ..models import Product, Interaction, Action, ProductCategoryDetail
from datetime import datetime
from sqlalchemy import text, func, case
from ..recommender import recommend_products

# Homepage route
@main.route("/", methods=["GET"])
def index():

    popular_products = (
        db.session.query(Product, func.count(Interaction.product_id).label("views"))
        .outerjoin(Interaction)
        .group_by(Product.id)
        .order_by(text("views DESC"))
    )
    # Get categories for category banners
    categories = {}

    for product in popular_products:
        if len(categories) >= current_app.config["CATEGORY_BANNERS"]:
            break
        for category in product.Product.categories:
            if len(categories) >= current_app.config["CATEGORY_BANNERS"]:
                break
            if category.category.id not in categories:
                categories[category.category.id] = category.category.name

    popular_products = popular_products.limit(current_app.config["PRODUCT_IN_CAROUSEL"])

    rec_products = []
    if current_user.is_authenticated:
        # use purchase history for personalized recommendation
        purchase_action = Action.query.filter_by(name="purchase").first().id

        purchased_ids = [
            i.product_id
            for i in Interaction.query.filter_by(
                action_type_id=purchase_action, user_id=current_user.id
            ).order_by(Interaction.timestamp.asc())
        ] # [oldest, ..., newest]
        # print(purchased_ids)
        print(current_user.id)

        if len(purchased_ids) > 0:
            rec_ids = recommend_products(purchased_ids) 

            whens = {id: index for index, id in enumerate(rec_ids)}
            sort_logic = case(value=Product.id, whens=whens)
            rec_products = (
                db.session.query(Product)
                .filter(Product.id.in_(list(rec_ids)))
                .order_by(sort_logic)
                .limit(current_app.config["PRODUCT_IN_CAROUSEL"])
            ).all()

    return render_template(
        "index.html",
        popular_products=popular_products,
        recently_viewed_products=popular_products,
        recommend_products=rec_products,
        categories=categories,
    )



@main.route("/product/<id>", methods=["GET"])
def product(id):
    product = Product.query.filter_by(id=id).first_or_404()
    recently_products = []
    views = []

    # Save to session
    views = session.get("viewed", [])
    view_found = dict(views).get(id, None)

    if view_found is not None:
        views.pop(views.index((id, view_found)))

    # the interaction in the session is stored in [oldest, ..., newest]
    views.append((id, datetime.now().timestamp()))

    # Limit session views
    limit_session_view = current_app.config["SESSION_VIEWS_LIMIT"]
    if len(views) > limit_session_view:
        views = views[-limit_session_view:]
    session["viewed"] = views


    if current_user.is_authenticated:
        view_id = Action.query.filter_by(name="view").first().id

        i = Interaction(user=current_user, product=product, action_type_id=view_id)
        db.session.add(i)
        db.session.commit()

        recently_products = (
            Product.query.join(Interaction)
            .filter(
                Interaction.user_id == current_user.id,
                Interaction.action_type_id == view_id,
            )
            .order_by(Interaction.timestamp.desc())
            .limit(current_app.config["PRODUCT_IN_CAROUSEL"])
        )
    else:
        whens = dict(views)
        sort_logic = case(value=Product.id, whens=whens)
        recently_products = Product.query.filter(
            Product.id.in_([id for id, ts in views])
        ).order_by(sort_logic.desc())

    # Use view interaction for session-based recommendation
    view_ids = [id for id, ts in views]

    rec_ids = recommend_products(view_ids)

    whens = {id: index for index, id in enumerate(rec_ids)}
    sort_logic = case(value=Product.id, whens=whens)

    rec_products = (
        db.session.query(Product)
        .filter(Product.id.in_(list(rec_ids)))
        .order_by(sort_logic)
        .limit(current_app.config["PRODUCT_IN_CAROUSEL"])
    ).all()

    return render_template(
        "product/detail.html",
        product=product,
        recently_products=recently_products,
        recommend_products=rec_products,
    )


# Find products by category, name, price,...
@main.route("/products/", methods=["GET"])
@main.route("/search/<key>", methods=["GET"])
def search(key=None):
    # Filter products
    category = request.args.get("c", "", type=str).replace(" ", "")

    query = Product.query

    if len(category) > 0:
        categories = category.split(",")
        query = query.join(ProductCategoryDetail)
        for c in categories:
            # remove item don't have category
            query = query.filter(
                Product.categories.any(ProductCategoryDetail.category_id == c)
            )


    if key is not None:
        key = key.replace("%", "").replace("*", "").replace("?", "")

        query = query.filter(
            Product.name.ilike("%" + key + "%")
            | Product.brand.ilike("%" + key + "%")
            | Product.id.ilike("%" + key + "%")
        )

    # Sort products
    sort = request.args.get("sort", -1, type=int) 
    if sort == 0:
        query = query.order_by(Product.price.desc())
    if sort == 1:
        query = query.order_by(Product.price.asc())
    if sort == 2:
        query = (
            query.outerjoin(Interaction)
            .group_by(Product.id)
            .order_by(text("COUNT(products.asin) DESC"))
        )
    if sort == 3:
        query = query.order_by(Product.created_at.desc())

    # get the current page
    page = request.args.get("page", 1, type=int)

    pagination = query.paginate(
        page, per_page=current_app.config["PRODUCT_PER_PAGE"], error_out=False
    )

    # get products from pagination
    products = pagination.items

    categories = {}
    for product in query:
        if len(categories) >= current_app.config.get("CATEGORY_FILTER_LIMIT"):
            break 
        for c in product.categories:
            if len(categories) >= current_app.config.get("CATEGORY_FILTER_LIMIT"):
                break
            categories[c.category.id] = c.category.name

    return render_template(
        "product/search.html",
        products=products,
        pagination=pagination,
        key=key,
        c=category,
        categories=categories,
        sort=sort,
    )


# Change recommender model
@main.route("/change-recommender/<int:index>", methods=["GET"])
def change_recommender(index=-1):
    # index (0: sasrec, 1: bert4rec)
    if index > -1:
        session["recommender"] = index
    print("Change recommender to", index)
    next = request.args.get("next")
    if next is None or not next.startswith("/"):
        next = url_for("main.index")
    return redirect(next)


# view history / session actions
@main.route("/history", methods=["GET"])
def history():
    if current_user.is_anonymous:
        return abort(404)

    type = request.args.get("type", 0, type=int) # 0: all history, 1: current session
    print("type", type)

    query = current_user.actions.order_by(Interaction.timestamp.desc())


    if type == 1:
        views = session.get("viewed", [])
        add_to_cart = session.get("added", [])

        # last interaction
        ts_min = ts_view = ts_add = datetime.now().timestamp()

        if len(views) > 0:
            id, ts_view = views[-1]
        if len(add_to_cart) > 0:
            id, ts_add = add_to_cart[-1]

        ts_min = min(ts_min, ts_view, ts_add)
        query = query.filter(Interaction.timestamp > datetime.fromtimestamp(ts_view))

    # print(query.statement)
    page = request.args.get("page", 1, type=int)

    pagination = query.paginate(
        page, per_page=current_app.config["INTERACTION_PER_PAGE"], error_out=False
    )

    interactions = pagination.items

    return render_template(
        "history.html", interactions=interactions, pagination=pagination, type=type
    )
