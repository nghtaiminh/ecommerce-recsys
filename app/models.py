from datetime import datetime
from flask import json, current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
import csv


# Table user
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, default="User NoName")
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column("password", db.String(255))
    email = db.Column(db.String(255))
    address = db.Column(db.Text, default="")
    created_at = db.Column(db.Date, default=datetime.now)
    updated_at = db.Column(db.Date, default=datetime.now)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), default=1)
    active = db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", backref="user", lazy="dynamic")
    actions = db.relationship("Interaction", backref="user", lazy="dynamic")
    basket = db.relationship("Basket", backref="user", lazy="dynamic")

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User %r>" % self.username



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Table Roles
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.Date, default=datetime.now)
    updated_at = db.Column(db.Date, default=datetime.now)

    users = db.relationship("User", backref="role", lazy="dynamic")

    @staticmethod
    def insert_roles():
        roles = ["User", "Administrator"]
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
                db.session.add(role)
        db.session.commit()



class Product(db.Model):
    __tablename__ = "products"
    id = db.Column("asin", db.String(64), primary_key=True)
    name = db.Column(db.Text)

    categories = db.relationship(
        "ProductCategoryDetail", backref="product", lazy="dynamic"
    )

    brand = db.Column(db.Text)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=0)

    image = db.Column("image_url", db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)

    actions = db.relationship("Interaction", backref="product", lazy="dynamic")
    basket = db.relationship("Basket", backref="product", lazy="dynamic")
    orders = db.relationship("OrderDetail", backref="product", lazy="dynamic")

    def __repr__(self):
        return "<Product %r>" % self.id
    
    @staticmethod
    def load_data_json(filepath):
        try:
            data_json = json.load(open(filepath))
        except:
            print("Error: File not found!")

        for data in data_json:
            if (
                Product.query.filter_by(id=data.get("asin", "unknown")).first()
                is not None
            ):
                continue

            product = Product(
                id=data.get("asin", "unknown"),
                name=data.get("title", "unknown"),
                description=data.get("description", "unknown"),
                brand=data.get("brand", "unknown"),
                price=data.get("price", 0),
                image=data.get("imageURL", "unknown"),
            )
            db.session.add(product)

            for category in data.get("category", []):
                # Get category in db
                c = Category.query.filter_by(name=category).first()

                if c is None:
                    c = Category(name=category)
                    db.session.add(c)
                    db.session.flush()


                p_c_detail = ProductCategoryDetail(product=product, category=c)
                db.session.add(p_c_detail)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()



# Table category
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    products = db.relationship(
        "ProductCategoryDetail", backref="category", lazy="dynamic"
    )

    def __repr__(self):
        return "<Category %r>" % self.name


# Table Product - category
class ProductCategoryDetail(db.Model):
    __tablename__ = "product_category_detail"
    product_id = db.Column(
        "asin", db.String(64), db.ForeignKey("products.asin"), primary_key=True
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), primary_key=True
    )


class Action(db.Model):
    __tablename__ = "action_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    interactions = db.relationship("Interaction", backref="action_type", lazy="dynamic")

    def __repr__(self):
        return "<Action %r>" % self.name

    @staticmethod
    def insert_actions():
        actions = ["view", "add_to_cart", "purchase"]
        for a in actions:
            action = Action.query.filter_by(name=a).first()
            if action is None:
                action = Action(name=a)
                db.session.add(action)
        db.session.commit()


class Interaction(db.Model):
    __tablename__ = "user_interactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    product_id = db.Column(
        "product_asin", db.String(64), db.ForeignKey("products.asin")
    )
    action_type_id = db.Column(db.Integer, db.ForeignKey("action_types.id"), default=1)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return "<Interaction %r>" % self.id
    
    @staticmethod
    def load_data(filepath):
        try:
            data_csv = csv.reader(open(filepath))
            next(data_csv, None)  # skip the headers
        except:
            print("Error: File not found!")

        count = 0
        purchase_action = Action.query.filter_by(name="purchase").first().id
        for data in data_csv:
            count += 1

            if count >= 51022:
                break

            u = User.query.filter_by(id=data[1]).first()
            if u is None:
                # Add fake user
                u = User(
                    name="user " + data[1],
                    username="user" + data[1],
                    password="123456",
                    email="user" + data[1] + "@example.com",
                    address="12 Fake Address",
                )
                db.session.add(u)
                db.session.flush()

                while str(u.id) < data[1]:
                    u = User(
                        name="user " + data[1],
                        username="user" + data[1],
                        password="123456",
                        email="user" + data[1] + "@example.com",
                        address="12 Fake Address",
                    )
                    db.session.add(u)
                    db.session.flush()

            p = Product.query.filter_by(id=data[0]).first()
            if p is not None:
                i = Interaction(
                    user=u,
                    product=p,
                    action_type_id=purchase_action,
                    timestamp=datetime.fromtimestamp(float(data[3])),
                )
                db.session.add(i)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()




class Basket(db.Model):
    __tablename__ = "basket_products"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    product_id = db.Column(
        "asin", db.String(64), db.ForeignKey("products.asin"), primary_key=True
    )
    quantity = db.Column(db.Integer, default=1)

    def __repr__(self):
        return "<Basket of user %r>" % self.user_id



class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    products = db.relationship("OrderDetail", backref="order", lazy="dynamic")

    def __repr__(self):
        return "<Order %r>" % self.id


class OrderDetail(db.Model):
    __tablename__ = "order_product_detail"
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), primary_key=True)
    product_id = db.Column(
        "asin", db.String(64), db.ForeignKey("products.asin"), primary_key=True
    )
    quantity = db.Column(db.Integer, default=1)

    def __repr__(self):
        return "<OrderDetail %r>" % self.order_id
