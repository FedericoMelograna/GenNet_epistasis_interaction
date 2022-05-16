import os
import sys
import warnings

import matplotlib

warnings.filterwarnings('ignore')
matplotlib.use('agg')
sys.path.insert(1, os.path.dirname(os.getcwd()) + "/GenNet_utils/")
import tensorflow as tf
import tensorflow.keras as K

tf.keras.backend.set_epsilon(0.0000001)
from GenNet_utils.Dataloader import *
from GenNet_utils.Utility_functions import *
from GenNet_utils.Create_network import *
from GenNet_utils.Create_plots import *


def weighted_binary_crossentropy(y_true, y_pred):
    y_true = K.backend.clip(tf.cast(y_true, dtype=tf.float32), 0.0001, 1)
    y_pred = K.backend.clip(tf.cast(y_pred, dtype=tf.float32), 0.0001, 1)

    return K.backend.mean(
        -y_true * K.backend.log(y_pred + 0.0001) * weight_positive_class - (1 - y_true) * K.backend.log(
            1 - y_pred + 0.0001) * weight_negative_class)


def train_classification(args):
    model = None
    masks = None
    datapath = args.path
    jobid = args.ID
    wpc = args.wpc
    lr_opt = args.learning_rate
    batch_size = args.batch_size
    epochs = args.epochs
    l1_value = args.L1
    problem_type = args.problem_type
    patience = args.patience

    if args.genotype_path == "undefined":
        genotype_path = datapath
    else:
        genotype_path = args.genotype_path

    if args.mixed_precision == True:
        use_mixed_precision()

    check_data(datapath=datapath, genotype_path=genotype_path, mode=problem_type)

    global weight_positive_class, weight_negative_class

    weight_positive_class = wpc
    weight_negative_class = 1

    optimizer_model = tf.keras.optimizers.Adam(lr=lr_opt)

    train_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 1)
    val_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 2)
    test_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 3)
    num_covariates = pd.read_csv(datapath + "subjects.csv").filter(like='cov_').shape[1]
    val_size_train = val_size

    if args.epoch_size is None:
        args.epoch_size = train_size
    else:
        val_size_train = args.epoch_size // 2
        print("Using each epoch", args.epoch_size,"randomly selected training examples")
        print("Validation set size used during training is also set to half the epoch_size")

    inputsize = get_inputsize(genotype_path)

    folder, resultpath = get_paths(args)

    print("weight_possitive_class", weight_positive_class)
    print("weight_possitive_class", weight_negative_class)
    print("jobid =  " + str(jobid))
    print("folder = " + str(folder))
    print("batchsize = " + str(batch_size))
    print("lr = " + str(lr_opt))

    if args.network_name == "lasso":
        print("lasso network")
        model, masks = lasso(inputsize=inputsize, l1_value=l1_value)
    else:
        if os.path.exists(datapath + "/topology.csv"):
            model, masks = create_network_from_csv(datapath=datapath, inputsize=inputsize, genotype_path=genotype_path,
                                                   l1_value=l1_value, num_covariates=num_covariates)
        if len(glob.glob(datapath + "/*.npz")) > 0:
            model, masks = create_network_from_npz(datapath=datapath, inputsize=inputsize, genotype_path=genotype_path,
                                                   l1_value=l1_value, num_covariates=num_covariates, mask_order=args.mask_order)

    model.compile(loss=weighted_binary_crossentropy, optimizer=optimizer_model,
                  metrics=["accuracy", sensitivity, specificity])

    with open(resultpath + '/model_architecture.txt', 'w') as fh:
        model.summary(print_fn=lambda x: fh.write(x + '\n'))

    csv_logger = K.callbacks.CSVLogger(resultpath + 'train_log.csv', append=True)
    early_stop = K.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.0001, patience=patience, verbose=1, mode='auto',
                                           restore_best_weights=True)
    save_best_model = K.callbacks.ModelCheckpoint(resultpath + "bestweights_job.h5", monitor='val_loss',
                                                  verbose=1, save_best_only=False, mode='auto')

    
    if os.path.exists(resultpath + '/bestweights_job.h5') and not(args.resume):
        print('Model already Trained')       
    elif os.path.exists(resultpath + '/bestweights_job.h5') and args.resume:
        print("Resuming already Trained mode")
        model.load_weights(resultpath + '/bestweights_job.h5')
        train_generator = TrainDataGenerator(datapath=datapath,
                                             genotype_path=genotype_path,
                                             batch_size=batch_size,
                                             trainsize=int(train_size),
                                             inputsize=inputsize,
                                             epoch_size=args.epoch_size)
        history = model.fit_generator(
            generator=train_generator,
            shuffle=True,
            epochs=epochs,
            verbose=1,
            callbacks=[early_stop, save_best_model, csv_logger],
            workers=1,
            use_multiprocessing=False,
            validation_data=EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size,
                                          setsize=val_size_train,
                                          inputsize=inputsize, evalset="validation")

        )

        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'val'], loc='upper left')
        plt.savefig(resultpath + "train_val_loss.png")
        plt.show()
    else:
        print("Start training from scratch")
        train_generator = TrainDataGenerator(datapath=datapath,
                                             genotype_path=genotype_path,
                                             batch_size=batch_size,
                                             trainsize=int(train_size),
                                             inputsize=inputsize,
                                             epoch_size=args.epoch_size)
        history = model.fit_generator(
            generator=train_generator,
            shuffle=True,
            epochs=epochs,
            verbose=1,
            callbacks=[early_stop, save_best_model, csv_logger],
            workers=1,
            use_multiprocessing=False,
            validation_data=EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size,
                                          setsize=val_size_train,
                                          inputsize=inputsize, evalset="validation")

        )

        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'val'], loc='upper left')
        plt.savefig(resultpath + "train_val_loss.png")
        plt.show()

    model.load_weights(resultpath + '/bestweights_job.h5')
    print("Finished")
    print("Analysis over the validation set")
    pval = model.predict_generator(
        EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size, setsize=val_size,
                      inputsize=inputsize,
                      evalset="validation"))
    yval = get_labels(datapath, set_number=2)
    auc_val, confusionmatrix_val = evaluate_performance(yval, pval)
    np.save(resultpath + "/pval.npy", pval)

    print("Analysis over the test set")
    ptest = model.predict_generator(
        EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size, setsize=test_size,
                      inputsize=inputsize, evalset="test"))
    ytest = get_labels(datapath, set_number=3)
    auc_test, confusionmatrix_test = evaluate_performance(ytest, ptest)
    np.save(resultpath + "/ptest.npy", ptest)

    data = {'Jobid': [args.ID],
            'Datapath': [str(args.path)],
            'genotype_path': [str(genotype_path)],
            'Batchsize': [args.batch_size],
            'Learning rate': [args.learning_rate],
            'L1 value': [args.L1],
            'patience': [args.patience],
            'epoch size': [args.epoch_size],
            'epochs': [args.epochs],
            'Weight positive class': str(args.wpc),
            'AUC validation': [auc_val],
            'AUC test': [auc_test]}
    pd_summary_row = pd.DataFrame(data)
    pd_summary_row.to_csv(resultpath + "/Summary_results.csv")

    with open(resultpath + '/Results_' + str(jobid) + '.txt', 'a') as f:
        f.write('\n Jobid = ' + str(jobid))
        f.write('\n Batchsize = ' + str(batch_size))
        f.write('\n Weight positive class = ' + str(weight_positive_class))
        f.write('\n Weight negative class= ' + str(weight_negative_class))
        f.write('\n Learningrate = ' + str(lr_opt))
        f.write('\n Optimizer = ' + str(optimizer_model))
        f.write('\n L1 value = ' + str(l1_value))
        f.write('\n')
        f.write("Validation set")
        f.write('\n Score auc = ' + str(auc_val))
        f.write('\n Confusion matrix:')
        f.write(str(confusionmatrix_val))
        f.write('\n')
        f.write("Test set")
        f.write('\n Score auc = ' + str(auc_test))
        f.write('\n Confusion matrix ')
        f.write(str(confusionmatrix_test))

    if os.path.exists(datapath + "/topology.csv"):
        importance_csv = create_importance_csv(datapath, model, masks)
        importance_csv.to_csv(resultpath + "connection_weights.csv")


def train_regression(args):
    model = None
    masks = None
    datapath = args.path
    jobid = args.ID
    lr_opt = args.learning_rate
    batch_size = args.batch_size
    epochs = args.epochs
    l1_value = args.L1
    problem_type = args.problem_type
    patience = args.patience
    

    if args.genotype_path == "undefined":
        genotype_path = datapath
    else:
        genotype_path = args.genotype_path

    check_data(datapath=datapath, genotype_path=genotype_path, mode=problem_type)

    optimizer_model = tf.keras.optimizers.Adam(lr=lr_opt)

    train_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 1)
    val_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 2)
    test_size = sum(pd.read_csv(datapath + "subjects.csv")["set"] == 3)
    num_covariates = pd.read_csv(datapath + "subjects.csv").filter(like='cov_').shape[1]
    inputsize = get_inputsize(genotype_path)
    val_size_train = val_size

    if args.epoch_size is None:
        args.epoch_size = train_size
    else:
        val_size_train = args.epoch_size // 2
        print("Using each epoch", args.epoch_size,"randomly selected training examples")
        print("Validation set size used during training is also set to half the epoch_size")


    folder, resultpath = get_paths(args)

    print("jobid =  " + str(jobid))
    print("folder = " + str(folder))
    print("batchsize = " + str(batch_size))
    print("lr = " + str(lr_opt))

    if args.network_name == "lasso":
        print("lasso network")
        model, masks = lasso(inputsize=inputsize, l1_value=l1_value)
    elif args.network_name == "regression_height":
        print("regression_height network")
        model, masks = regression_height(inputsize=inputsize, l1_value=l1_value)
    else:
        if os.path.exists(datapath + "/topology.csv"):
            model, masks = create_network_from_csv(datapath=datapath, inputsize=inputsize, genotype_path=genotype_path,
                                                   l1_value=l1_value, regression=True, num_covariates=num_covariates)
        if len(glob.glob(datapath + "/*.npz")) > 0:
            model, masks = create_network_from_npz(datapath=datapath, inputsize=inputsize, genotype_path=genotype_path,
                                                   l1_value=l1_value, regression=True, num_covariates=num_covariates)

    model.compile(loss="mse", optimizer=optimizer_model,
                  metrics=["mse"])

    with open(resultpath + '/model_architecture.txt', 'w') as fh:
        model.summary(print_fn=lambda x: fh.write(x + '\n'))

    early_stop = K.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.0001, patience=patience, verbose=1, mode='auto',
                                           restore_best_weights=True)
    save_best_model = K.callbacks.ModelCheckpoint(resultpath + "bestweights_job.h5", monitor='val_loss',
                                                  verbose=1, save_best_only=True, mode='auto')
    csv_logger = K.callbacks.CSVLogger(resultpath + 'train_log.csv', append=True)

    if os.path.exists(resultpath + '/bestweights_job.h5') and not(args.resume):
        print('Model already trained')
    elif os.path.exists(resultpath + '/bestweights_job.h5') and args.resume:
        print("Resuming trainine")
        model.load_weights(resultpath + '/bestweights_job.h5')
        history = model.fit_generator(
            generator=TrainDataGenerator(datapath=datapath,
                                         genotype_path=genotype_path,
                                         batch_size=batch_size,
                                         trainsize=int(train_size),
                                         inputsize=inputsize,
                                         epoch_size=args.epoch_size),
            shuffle=True,
            epochs=epochs,
            verbose=1,
            callbacks=[early_stop, save_best_model, csv_logger],
            workers=1,
            use_multiprocessing=False,
            validation_data=EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size,
                                          setsize=val_size_train, inputsize=inputsize, evalset="validation")
        )
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'val'], loc='upper left')
        plt.savefig(resultpath + "train_val_loss.png")
        plt.show()      
     
    else:
        print("Start training from scratch")
        history = model.fit_generator(
            generator=TrainDataGenerator(datapath=datapath,
                                         genotype_path=genotype_path,
                                         batch_size=batch_size,
                                         trainsize=int(train_size),
                                         inputsize=inputsize,
                                         epoch_size=args.epoch_size),
            shuffle=True,
            epochs=epochs,
            verbose=1,
            callbacks=[early_stop, save_best_model, csv_logger],
            workers=1,
            use_multiprocessing=False,
            validation_data=EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size,
                                          setsize=val_size_train, inputsize=inputsize, evalset="validation")
        )
        plt.plot(history.history['loss'])
        plt.plot(history.history['val_loss'])
        plt.title('model loss')
        plt.ylabel('loss')
        plt.xlabel('epoch')
        plt.legend(['train', 'val'], loc='upper left')
        plt.savefig(resultpath + "train_val_loss.png")
        plt.show()

    model.load_weights(resultpath + '/bestweights_job.h5')
    print("Finished")
    print("Analysis over the validation set")
    pval = model.predict_generator(
        EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size, setsize=val_size,
                      evalset="validation", inputsize=inputsize))
    yval = get_labels(datapath, set_number=2)
    fig, mse_val, explained_variance_val, r2_val = evaluate_performance_regression(yval, pval)
    np.save(resultpath + "/pval.npy", pval)
    fig.savefig(resultpath + "/validation_predictions.png", bbox_inches='tight', pad_inches=0)

    print("Analysis over the test set")
    ptest = model.predict_generator(
        EvalGenerator(datapath=datapath, genotype_path=genotype_path, batch_size=batch_size, setsize=test_size,
                      inputsize=inputsize, evalset="test"))
    ytest = get_labels(datapath, set_number=3)
    fig, mse_test, explained_variance_test, r2_test = evaluate_performance_regression(ytest, ptest)
    np.save(resultpath + "/ptest.npy", ptest)
    fig.savefig(resultpath + "/test_predictions.png", bbox_inches='tight', pad_inches=0)

    data = {'Jobid': [args.ID],
            'Datapath': [str(args.path)],
            'genotype_path': [str(genotype_path)],
            'Batchsize': [args.batch_size],
            'Learning rate': [args.learning_rate],
            'L1 value': [args.L1],
            'patience': [args.patience],
            'epoch size': [args.epoch_size],
            'epochs': [args.epochs],
            'MSE validation': [mse_val],
            'MSE test': [mse_test],
            'Explained variance val': [explained_variance_val],
            'Explained variance test': [explained_variance_test]}
    pd_summary_row = pd.DataFrame(data)
    pd_summary_row.to_csv(resultpath + "/Summary_results.csv")

    with open(resultpath + '/Results_' + str(jobid) + '.txt', 'a') as f:
        f.write('\n Jobid = ' + str(jobid))
        f.write('\n Batchsize = ' + str(batch_size))
        f.write('\n Learningrate = ' + str(lr_opt))
        f.write('\n Optimizer = ' + str(optimizer_model))
        f.write('\n L1 value = ' + str(l1_value))
        f.write('\n')
        f.write("Validation set")
        f.write('\n Mean squared error = ' + str(mse_val))
        f.write('\n Explained variance = ' + str(explained_variance_val))
        f.write('\n R2 = ' + str(r2_val))
        f.write("Test set")
        f.write('\n Mean squared error = ' + str(mse_test))
        f.write('\n Explained variance = ' + str(explained_variance_val))
        f.write('\n R2 = ' + str(r2_test))

    if os.path.exists(datapath + "/topology.csv"):
        importance_csv = create_importance_csv(datapath, model, masks)
        importance_csv.to_csv(resultpath + "connection_weights.csv")
