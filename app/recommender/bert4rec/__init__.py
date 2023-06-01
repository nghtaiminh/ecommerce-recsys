import argparse
import torch
import numpy as np
from flask import current_app

from .bert import BERTModel

parser = argparse.ArgumentParser()


# set up the parameters for the model
parser.add_argument('--model_init_seed', type=int, default=0)
parser.add_argument('--bert_max_len', type=int, default=100,
                    help='Length of sequence for bert')
parser.add_argument('--num_items', type=int, default=51022,
                    help='Number of total items')
parser.add_argument('--bert_hidden_units', type=int,
                    default=256, help='Size of hidden vectors (d_model)')
parser.add_argument('--bert_num_blocks', type=int, default=2,
                    help='Number of transformer layers')
parser.add_argument('--bert_num_heads', type=int, default=4,
                    help='Number of heads for multi-attention')
parser.add_argument('--bert_dropout', type=float, default=0.4,
                    help='Dropout probability to use throughout the model')
parser.add_argument('--bert_mask_prob', type=float, default=0.5,
                    help='Probability for masking items in the training sequence')


def create_model():
    args = parser.parse_args()
    model = BERTModel(args)
    path = 'app/recommender/bert4rec/bert4rec_model.pth'
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_state_dict = torch.load(path, map_location=device)[
        'model_state_dict']
    model.load_state_dict(model_state_dict)
    model.eval()

    return model


def recommend(interaction_seq, candidate_items=None, k=12, exclude_interacted=True):
    """
    Give recommendations for a input sequence on how likely the user will interact next

    Args:
        seq : 1D array 
            Interaction sequence of the user. List of item IDs sorted by timestamp in ascending order [oldest, ..., newest]
        candidate_items : 1D array, (optional)  
            List of IDs of items the model should predict. If None, the model will predict for all items.
        k : int, (optional): 
            Number of recommendations.
        exclude_interacted: bool, (optional)
            Whether to exclude interacted items which are in 'seq'.
    Returns:
        recommendations : 1D array 
            List of recommended item ids. Ranked from most relevant to least relevant.
    """
    # map the item indices to the model's item indices
    interaction_seq = [current_app.bert4rec_itemmap[x] for x in interaction_seq]
    # prepare the input sequence
    interaction_seq = interaction_seq + [current_app.bert4rec.args.num_items + 1]
    interaction_seq = interaction_seq[-current_app.bert4rec.args.bert_max_len:]
    padding_len = current_app.bert4rec.args.bert_max_len - len(interaction_seq)
    interaction_seq = [0] * padding_len + interaction_seq
    interaction_seq = torch.LongTensor(interaction_seq).unsqueeze(0)
    # score the items
    with torch.no_grad():
        scores = current_app.bert4rec(interaction_seq)
    scores = scores[:, -1, :]

    # exclude interacted items
    if exclude_interacted:
        if candidate_items:
            candidates = [x for x in range(1, len(current_app.bert4rec_itemmap)+1)
                          if x not in interaction_seq and x in candidate_items]
        else:
            candidates = [x for x in range(1, len(current_app.bert4rec_itemmap)+1) if x not in interaction_seq]
        
        candidate = torch.LongTensor(candidates).unsqueeze(0).to(scores.device)
        scores = scores.gather(1, candidate)

    # get the top k items
    topk = torch.topk(scores, k=k).indices.squeeze(0).tolist()

    # map to the original item indices
    def get_key(val):
        for key, value in current_app.bert4rec_itemmap.items():
            if val == value:
                return key
            
    recommendations = [get_key(x) for x in topk]

    return recommendations
