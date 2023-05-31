from . import sasrec
from . import sasrec, bert4rec
from flask import session

recommenders = [
    {"model": sasrec, "name": "SASRec"},
    {"model": bert4rec, "name": "BERT4Rec"},
]

def recommend_products(input):
    # Recommend products based on the recommender selected by the user
    output = recommenders[session.get("recommender", 0)].get('model').recommend(input)
    return output


