import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from interpretation.weight_importance import make_importance_values_input
from interpretation.NID import Get_weight_tsang, GenNet_pairwise_interactions_topn
from interpretation.RLIPP import calculate_RLIPP

from GenNet_utils.Utility_functions import get_SLURM_id, evaluate_performance
from GenNet_utils.Train_network import load_trained_network

def interpret(args):
    if args.type == 'get_weight_scores':
        get_weight_scores(args)
    elif args.type == 'NID':
        get_NID_scores(args)
    elif args.type == 'RLIPP':
        get_RLIPP_scores(args)
    elif args.type == 'DFIM':
        get_DFIM_scores(args)
    else:
        print("invalid type:", args.type)
        exit()


def get_weight_scores(args):
    model, masks = load_trained_network(args)

    if os.path.exists(args.resultpath + "/weight_importance.npy"):
        print('weight Done')
    else:
        weight_importance = make_importance_values_input(model, masks=masks)
        np.save(args.resultpath + "/weight_importance.npy", weight_importance)


def get_NID_scores(args):
    model, masks = load_trained_network(args)

    if args.layer == "None":
        if args.one_hot == 1:
            interp_layer = 3
        else:
            interp_layer = 2
    else:
        interp_layer = args.layer

    if os.path.exists(args.resultpath + "/NID.csv"):
        print('RLIPP Done')
        interaction_ranking = pd.read_csv(args.resultpath + "/NID.csv")
    else:
        w_in, w_out = Get_weight_tsang(model, interp_layer, masks)
        interaction_ranking1 = GenNet_pairwise_interactions_topn(w_in[:,1] ,w_out[:,1], masks, n=4)
        interaction_ranking2 = GenNet_pairwise_interactions_topn(w_in[:,0] ,w_out[:,0], masks, n=4)

        interaction_ranking = interaction_ranking1.append(interaction_ranking2)
        interaction_ranking = interaction_ranking.sort_values("strength", ascending =False)
        interaction_ranking.to_csv(args.resultpath + "/NID.csv")
  
    return interaction_ranking



def get_RLIPP_scores(args):
    print("not implemented yet")



def get_DFIM_scores(args):
    print("not implemented yet")