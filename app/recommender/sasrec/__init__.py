from flask import current_app
import torch
import numpy as np
from .model import SASRec

import argparse


def str2bool(s):
    if s not in {'false', 'true'}:
        raise ValueError('Not a valid boolean string')
    return s == 'true'


parser = argparse.ArgumentParser()
parser.add_argument('--dataset', default='AmazonBooks_new', type=str)
parser.add_argument('--train_dir', default='default', type=str)
parser.add_argument('--batch_size', default=128, type=int)
parser.add_argument('--lr', default=0.001, type=float)
parser.add_argument('--maxlen', default=100, type=int)
parser.add_argument('--hidden_units', default=64, type=int)
parser.add_argument('--num_blocks', default=2, type=int)
parser.add_argument('--num_epochs', default=100, type=int)
parser.add_argument('--num_heads', default=1, type=int)
parser.add_argument('--dropout_rate', default=0.5, type=float)
parser.add_argument('--l2_emb', default=0.0, type=float)
parser.add_argument(
    '--device', default=torch.device('cuda' if torch.cuda.is_available() else 'cpu'), type=str)
parser.add_argument('--inference_only', default=True, type=str2bool)
parser.add_argument('--state_dict_path',
                    default='app/recommender/sasrec/sasrec_model.pth', type=str)


def create_model():
    args = parser.parse_args()
    model = SASRec(len(current_app.sasrec_usermap),
                   len(current_app.sasrec_itemmap), args)
    if args.state_dict_path is not None:
        try:
            model.load_state_dict(torch.load(
                args.state_dict_path, map_location=torch.device(args.device)))
        except:
            raise Exception('Load sasrec model failed')
    model.eval()
    return model


def recommend(interaction_seq, candidate_items=None, k=12, exclude_interacted=True):
    """
    Give recommendations for a input sequence on how likely the user will interact next

    Args:
        interaction_seq : 1D array 
            Interaction sequence of the user. List of item IDs sorted by timestamp in ascending order [oldest, ..., newest]
        candidate_items : 1D array, (optional)  
            List of IDs of items the model should give prediction scores. If None, the model will give prediction scores for all items.
        k : int, (optional): 
            Number of recommendations.
        exclude_interacted: bool, (optional)
            Whether to exclude interacted items which are in interaction_seq.
    Returns:
        recommendations : 1D array 
            List of recommended item ids. Ranked from most relevant to least relevant.
    """

    # map printthe user's interacted items to their indices
    # ('user_interacted_item_seq', user_interacted_item_seq)
    interaction_seq = [current_app.sasrec_itemmap[x]
                       for x in interaction_seq]

    seq = np.zeros([current_app.sasrec.args.maxlen], dtype=np.int32)
    idx = current_app.sasrec.args.maxlen - 1

    for i in reversed(interaction_seq):
        seq[idx] = i
        idx -= 1
        if idx == -1:
            break

    # if candidate are provided, map them to their indices, otherwise use all items
    if candidate_items:
        item_idx = [current_app.sasrec_itemmap[x] for x in candidate_items]
    else:
        item_idx = [x for x in range(1, len(current_app.sasrec_itemmap)+1)]

    if exclude_interacted:
        item_idx = [x for x in item_idx if x not in interaction_seq]

    predictions = -current_app.sasrec.predict(*[np.array(l) for l in [[seq], item_idx]])
    # predict the revelance score
    predictions = predictions[0]  # - for 1st argsort DESC
    # rank the items
    rank = predictions.argsort()[:k].tolist()
    # map the indices to their item ids

    def get_key(val):
        for key, value in current_app.sasrec_itemmap.items():
            if val == value:
                return key

    recommendations = [get_key(item) for item in rank]

    return recommendations
