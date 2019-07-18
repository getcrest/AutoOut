import glob
import time

import dask
import numpy as np
import pandas as pd
from dask import delayed
from distributed import LocalCluster, Client
from joblib import parallel_backend
from scipy.stats import zscore
from sklearn.cluster import DBSCAN, OPTICS
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, accuracy_score, precision_score, average_precision_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM


class ZScore(object):
    def __init__(self, threshold):
        self.threshold = threshold
        self.y_predicted = list()

    def fit(self, X):
        df = pd.DataFrame()
        for i in X.columns:
            df[i] = zscore(X[i], axis=0, ddof=1)
        df = df.abs()
        for i in range(df.shape[0]):
            if any(df.iloc[i] > self.threshold):
                self.y_predicted.append(1)
            else:
                self.y_predicted.append(0)

    def predict(self, X):
        pass

    def fit_predict(self, X):
        self.fit(X)
        return self.y_predicted


def detect(X, space):
    """
    Detect outliers
    """
    start_time = time.time()
    print("==================================================")
    print("Outlier detection and treatment started ...")
    print("Space:", space)

    y_predicted = None
    params = space['params']
    error = dict()

    try:
        if space['model'] == "DBSCAN":
            model = DBSCAN(**params)
            y_predicted = model.fit_predict(X)
            y_predicted = list(map(lambda x: 1 if x < 0 else 0, y_predicted))

        elif space['model'] == "OPTICS":
            model = OPTICS(**params)
            y_predicted = model.fit_predict(X)
            print(y_predicted)
            y_predicted = list(map(lambda x: 1 if x < 0 else 0, y_predicted))

        elif space['model'] == "EllipticEnvelope":
            model = EllipticEnvelope(**params)
            y_predicted = model.fit_predict(X)
            y_predicted = list(map(lambda x: 1 if x == -1 else 0, y_predicted))

        elif space['model'] == "IsolationForest":
            model = IsolationForest(**params)
            with parallel_backend('threading'):
                y_predicted = model.fit_predict(X)
            y_predicted = list(map(lambda x: 1 if x == -1 else 0, y_predicted))

        elif space['model'] == "OneClassSVM":
            model = OneClassSVM(**params)
            y_predicted = model.fit_predict(X)
            y_predicted = list(map(lambda x: 1 if x == -1 else 0, y_predicted))

        elif space['model'] == "LocalOutlierFactor":
            model = LocalOutlierFactor(**params)
            with parallel_backend('threading'):
                y_predicted = model.fit_predict(X)
            y_predicted = list(map(lambda x: 1 if x == -1 else 0, y_predicted))

        elif space['model'] == "zscore":
            model = ZScore(threshold=params['threshold'])
            y_predicted = model.fit_predict(X)

    except Exception as e:
        print("Error:", e)
        y_predicted = [0] * data_frame.shape[0]
        error['detect_' + str(space)] = e

    if isinstance(y_predicted, list):
        y_predicted = np.array(y_predicted)

    time_taken = time.time() - start_time
    print("Time taken:", time_taken)

    return y_predicted


def treat(X, y_preds, voting_percentage=0.6, threshold=0.1):
    """
    Treat outliers

    y_preds: list of lists

    1. Voting
    2. Remove outliers with 60% or more voting

    Don't remove more than 10% of values
    """
    df = pd.DataFrame(y_preds)
    sum_ = df.sum(axis=1, skipna=True)

    rows_to_remove = []

    for i, v in enumerate(sum_.tolist()):
        if v > voting_percentage * df.shape[1]:
            rows_to_remove.append({"index": i, "confidence": voting_percentage * df.shape[1]})

    nrows = X.shape[0]
    rows_to_remove_df = pd.DataFrame(rows_to_remove)
    if rows_to_remove_df.shape[0] > threshold * nrows:
        # Select only 10% rows
        rows_to_remove_df.sort_values('confidence', ascending=False).head((int)(threshold * nrows))

    if rows_to_remove_df.shape[0] > 0:
        X.drop(X.index[rows_to_remove_df['index']], inplace=True)

    print(X.shape)
    return X


def calculate_scores(y_predicted, y_true):
    """
    Function to calculate different performance scores
    """
    accuracy = accuracy_score(y_pred=y_predicted, y_true=y_true)
    precision = precision_score(y_pred=y_predicted, y_true=y_true)
    average_precision_score1 = average_precision_score(y_score=y_predicted, y_true=y_true)
    f1_score1 = f1_score(y_pred=y_predicted, y_true=y_true)

    print("Accuracy score:", accuracy)
    print("Precision score:", precision)
    print("Average Precision score:", average_precision_score1)
    print("F1 score:", f1_score1)
    print("Outlier detection and/or treatment completed.")

    return {"accuracy": accuracy,
            "precision": precision,
            "average_precision_score": average_precision_score1,
            "f1_score": f1_score1,
            }


if __name__ == '__main__':
    c = LocalCluster(processes=False, n_workers=2, threads_per_worker=3)
    dask_client = Client(c)

    delayed_tasks = []
    for index, dataset_path in enumerate(glob.glob("datasets/csv/*.csv")[:1]):
        spaces = [{"model": "zscore", "params": {}},
                  {"model": "DBSCAN", "params": {}},
                  # {"model": "OPTICS", "params": {}},
                  {"model": "IsolationForest", "params": {}},
                  {"model": "EllipticEnvelope", "params": {}},
                  {"model": "OneClassSVM", "params": {}},
                  {"model": "LocalOutlierFactor", "params": {}},
                  ]

        data_frame = pd.read_csv(dataset_path)
        print(data_frame.shape)

        try:
            data_frame = data_frame.drop(['label'], axis=1, inplace=False)
        except Exception as e:
            print("Error:", e)

        delayed_list = []
        for index, space in enumerate(spaces):
             delayed_list.append(delayed(detect)(data_frame, space))

        results = dask.compute(*delayed_list)
        final_results = dict(zip(range(len(list(results))), results))
        treated_dataframe = treat(data_frame, final_results)

    # all_results = dask.compute(*delayed_tasks)
    #
    # print(list(all_results))
    #
    # treat(data_frame, all_results)
    #
    # fdf = pd.DataFrame(list(all_results))
    # fdf.to_csv("results/{}.csv".format(time.time()))
    #
    # dask_client.close()
    # c.close()
