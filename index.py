import os
import pickle
from flask_migrate import Migrate
from flask import current_app

from app import create_app, db
from app.models import Product, Interaction, Role, Action
from app.recommender import sasrec, bert4rec


env = os.getenv("FLASK_CONFIG") or "development"
app = create_app(env)
migrate = Migrate(app, db)

json_path = os.getenv("JSON_PATH") or "data/products.json"   
rating_path = os.getenv("RATING_PATH") or "data/ratings.csv"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        Role.insert_roles()
        Action.insert_actions()
        # loading map files
        print("Loading artifacts...")
        current_app.sasrec_itemmap = pickle.load(open("app/recommender/sasrec/itemmap.pkl", "rb"))
        current_app.sasrec_usermap = pickle.load(open("app/recommender/sasrec/usermap.pkl", "rb"))
        current_app.bert4rec_itemmap = pickle.load(open("app/recommender/bert4rec/bert_itemmap.pkl", "rb"))
        current_app.bert4rec_usermap = pickle.load(open("app/recommender/bert4rec/bert_usermap.pkl", "rb"))
        # loading models and weights
        print("Creating model...")
        current_app.sasrec = sasrec.create_model()
        current_app.bert4rec = bert4rec.create_model()
        # load data ()
        print("Loading data...")
        if Product.query.count() < 1:
            Product.load_data_json(json_path)
            Interaction.load_data(rating_path)


    app.run()
