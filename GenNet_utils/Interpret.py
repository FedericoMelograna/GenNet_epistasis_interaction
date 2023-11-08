import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from interpretation.weight_importance import make_importance_values_input
from interpretation.NID import Get_weight_tsang, GenNet_pairwise_interactions_topn

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
    
    print("Interpreting with NID:")
    model, masks = load_trained_network(args)

    mask = masks[0]

    if args.layer == None:
        if args.onehot == 1:
            interp_layer = 3
        else:
            interp_layer = 2
    else:
        interp_layer = args.layer

    print("Interrpeting layer", interp_layer)
    if os.path.exists(args.resultpath + "/NID.csv"):
        print('RLIPP Done')
        interaction_ranking = pd.read_csv(args.resultpath + "/NID.csv")
    else:
        print("Obtaining the weights")
        w_in, w_out = Get_weight_tsang(model, interp_layer, masks)
        print("Computing interactions")

        pairwise_interactions_dfs = []
        for filter in range(w_in.shape[1]):  # for all the filters
            pairwise_interactions = GenNet_pairwise_interactions_topn(w_in[:,filter] ,w_out[:,filter], mask, n="auto")
            pairwise_interactions_dfs.append(pairwise_interactions)
        
        interaction_ranking = pd.concat(pairwise_interactions_dfs)
        interaction_ranking = interaction_ranking.sort_values("strength", ascending =False)
        interaction_ranking.to_csv(args.resultpath + "/NID.csv")
        print("NID results are saved in", args.resultpath + "/NID.csv")
  
    return interaction_ranking



def get_RLIPP_scores(args):
    print("not implemented yet")



def get_DFIM_scores(args):
    print("Interpreting with DFIM:")
    model, masks = load_trained_network(args)

    mask = masks[0]

    part_n = 0  # placeholder solution for multiprocessing


    if os.path.exists(args.resultpath  + "/DFIM_not_perturbed.npy"):
        print('DFIM Done')
        time_dfim = 0
    else:
        import shap
        import interpretation.DFIM as DFIM

        explainer  = shap.DeepExplainer((model.input, model.output), xval)

        importance = pd.read_csv(args.resultpath  + "/weight_importance.csv") # TODO check if exist otherwise run
        snp_index = np.array(importance.sort_values('percentage', ascending=False).index[:100])
        
        begin_index =  part_n * 25
        end_index =  (part_n + 1) * 25
        snp_index = snp_index[begin_index:end_index]
    
        perturbed_values, max_not_perturbed, loc_not_perturbed= DFIM.DFIM_test_index(explainer, xtest, snp_index) # use dataloader
        np.save(args.resultpath  + "/DFIM_not_perturbed_"+str(part_n)+".npy", max_not_perturbed)
        np.save(args.resultpath + "/DFIM_loc_not_perturbed_"+str(part_n)+".npy", loc_not_perturbed)
        np.save(args.resultpath + "/DFIM_perturbed_"+str(part_n)+".npy", perturbed_values)
        

    return 