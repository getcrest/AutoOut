import glob
import multiprocessing
import time

import dask
import numpy as np
import pandas as pd
from joblib import parallel_backend
from scipy.stats import zscore
from sklearn.cluster import DBSCAN, OPTICS
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.metrics import f1_score, accuracy_score, precision_score, average_precision_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from distributed import LocalCluster, Client
from dask import delayed


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


def train(data_frame, space, dataset_path):
    start_time = time.time()
    print("==================================================")
    print("Outlier detection and treatment started ...")
    print("Space:", space)
    print("Label column name:", data_frame.columns[-1])

    y = data_frame['label']
    X = data_frame.drop(['label'], axis=1)

    y_counts = y.value_counts()
    outlier_percentage = (y_counts.loc[0.0] / y_counts.sum()) * 100

    y_predicted = None
    params = space['params']
    fake_vote = 0
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
        error['detect_n_treat_outliers___' + str(space)] = e
        fake_vote += 1

    if isinstance(y_predicted, list):
        y_predicted = np.array(y_predicted)

    print(y_predicted.shape, y.shape)

    accuracy = accuracy_score(y_pred=y_predicted, y_true=y)
    precision = precision_score(y_pred=y_predicted, y_true=y)
    average_precision_score1 = average_precision_score(y_score=y_predicted, y_true=y)
    f1_score1 = f1_score(y_pred=y_predicted, y_true=y)

    print("Accuracy score:", accuracy_score(y_pred=y_predicted, y_true=y))
    print("Precision score:", precision_score(y_pred=y_predicted, y_true=y))
    print("Average Precision score:", average_precision_score(y_score=y_predicted, y_true=y))
    print("F1 score:", f1_score(y_pred=y_predicted, y_true=y))
    print("Outlier detection and/or treatment completed.")
    print("==================================================\n")

    time_taken = time.time() - start_time

    return {"accuracy": accuracy, "precision": precision, "average_precision_score": average_precision_score1,
            "f1_score": f1_score1, "time_taken": time_taken, 'algorithm': space['model'], 'params': space['params'],
            'outlier_percentage': outlier_percentage, 'samples': data_frame.shape[0], 'features': data_frame.shape[1],
            "dataset_path": dataset_path,
            }


if __name__ == '__main__':
    c = LocalCluster(processes=False, n_workers=2, threads_per_worker=3)
    dask_client = Client(c)

    # space = {"model": "DBSCAN",
    #          "params": {"eps": 0.5, "min_samples": 5,
    #                     "n_jobs": 3,
    #                     "algorithm": 'ball_tree', "metric": 'haversine'}
    #          }
    # space = {"model": "zscore", "params": {"threshold": 3.5}}
    space = {"model": "OPTICS", "params": {"n_jobs": 3}}

    delayed_tasks = []
    for index, dataset_path in enumerate(glob.glob("datasets/csv/*.csv")):
        data_frame = pd.read_csv(dataset_path)

        results = delayed(train)(data_frame, space, dataset_path)

        delayed_tasks.append(results)

    all_results = dask.compute(*delayed_tasks)

    print(list(all_results))

    fdf = pd.DataFrame(list(all_results))
    fdf.to_csv("results/{}.csv".format(time.time()))
