from .feed_forward import PositionwiseFeedForward
from .layer_norm import LayerNorm
from .sublayer import SublayerConnection
from .gelu import GELU

import random

import numpy as np
import torch
import torch.backends.cudnn as cudnn



def fix_random_seed_as(random_seed):
    random.seed(random_seed)
    torch.manual_seed(random_seed)
    torch.cuda.manual_seed_all(random_seed)
    np.random.seed(random_seed)
    cudnn.deterministic = True
    cudnn.benchmark = False