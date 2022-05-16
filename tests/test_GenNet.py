import os
import pandas as pd

from GenNet_utils.Create_plots import plot_layer_weight, manhattan_importance, sunburst_plot
from GenNet_utils.Utility_functions import get_paths

# import unittest
# TODO: add test without covariates
# TODO add test with covariates for regression + classification
# TODO add test with multiple genotype files.
# test randomnesss after .. epoch shuffles.


class ArgparseSimulator():
    def __init__(self,
                 path='/',
                 ID=999,
                 genotype_path='undefined',
                 network_name='undefined',
                 problem_type="classification",
                 wpc=1,
                 lr=0.01,
                 bs=10,
                 epochs=10,
                 L1=0.001,
                 patience = 10,
                 epoch_size = 100,
                 mixed_precision=False,
                 outfolder="undefined",
                 suffix=''):
        self.path = path
        self.ID = ID
        self.genotype_path = genotype_path
        self.network_name = network_name
        self.problem_type = problem_type
        self.wpc = wpc
        self.lr = lr
        self.learning_rate = lr
        self.bs = bs
        self.batch_size = bs
        self.epochs = epochs
        self.L1 = L1
        self.mixed_precision = mixed_precision
        self.out = outfolder
        self.suffix = suffix
        self.patience = patience
        self.epoch_size = epoch_size

def test_train_standard():
    value = os.system('cd .. && python GenNet.py train -path ./examples/example_study/ -ID 1000')
    assert value == 0


def test_train_regression():
    value = os.system('cd .. && python GenNet.py train -path ./examples/example_regression/ -ID 1001 -problem_type regression')
    assert value == 0


def test_train(datapath, jobid, wpc, lr_opt, batch_size, epochs, l1_value, problem_type, ):
    test1 = os.system(
        'cd .. && python GenNet.py train -path {datapath} -ID {jobid} -problem_type'
        ' {problem_type} -wpc {wpc} -lr {lr} -bs {bs}  -epochs {epochs} -L1 {L1}'.format(
            datapath=datapath, jobid=jobid, problem_type=problem_type, wpc=wpc, lr=lr_opt, bs=batch_size, epochs=epochs,
            L1=l1_value))

    args = ArgparseSimulator(path=datapath, ID=jobid, problem_type=problem_type, wpc=wpc, lr=lr_opt,
                        bs=batch_size, epochs=epochs, l1=l1_value)

    assert test1 == 0

    folder, resultpath = get_paths(args)
    test2 = os.path.exists(resultpath + '/bestweights_job.h5')
    assert test2


def test_convert():
    test1 = os.system(
        "python GenNet.py convert -g ./examples/A_to_Z/plink/"
        " -o ./examples/A_to_Z/processed_data/"
        "/  -study_name GenNet_simulation -step all")
    assert test1 == 0


def test_plot(exp_id):
    importance_csv = pd.read_csv(
        "results/GenNet_experiment_" + str(exp_id) + "/connection_weights.csv",
        index_col=0)
    resultpath = 'results/GenNet_experiment_' + str(exp_id) + '/'

    sunburst_plot(resultpath, importance_csv)
    manhattan_importance(resultpath, importance_csv)
    plot_layer_weight(resultpath, importance_csv, layer=0)
    plot_layer_weight(resultpath, importance_csv, layer=1)


if __name__ == '__main__':
    # test_train_standard()
    # test_train_regression()
    exp_id = 1
    test_plot(exp_id)
