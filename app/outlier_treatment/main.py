import glob
import json
import os
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
from sklearn.preprocessing import LabelEncoder, Normalizer
from sklearn.svm import OneClassSVM
import requests

from app.outlier_treatment.spaces import OUTLIER_SPACES


def encode_data(data_frame):
    for column_name in data_frame.columns:
        if str(data_frame[column_name].dtype) == 'object':
            label_encoder = LabelEncoder()
            data_frame[column_name] = label_encoder.fit_transform(data_frame[column_name])
    return data_frame


def data_cleaning_formatting(X):
    # Basic cleaning
    X = X.fillna(0)
    X = X.fillna('ffill')

    # Encode data
    X = encode_data(X)
    X = Normalizer().fit_transform(X)
    return X


class ZScore(object):
    def __init__(self, threshold=3.5):
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


# TODO: Put errors in the returned data
def detect(file_path, space, deleted_features):
    """
    Detect outliers
    """
    start_time = time.time()
    print("==================================================")
    print("Outlier detection and treatment started ...")
    print("Space:", space)

    X = pd.read_csv(file_path)

    if len(deleted_features) > 0:
        X = X.drop(deleted_features, axis=1, inplace=False)

    # Basic data cleaning
    X = data_cleaning_formatting(X)

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
        y_predicted = [0] * X.shape[0]
        error['detect_' + str(space)] = e

    if isinstance(y_predicted, list):
        y_predicted = np.array(y_predicted)

    time_taken = time.time() - start_time
    print("Time taken:", time_taken)

    return y_predicted


def treat(file_path, y_preds, experiment_id, media_root, voting_percentage=0.6, threshold=0.1):
    """
    Treat outliers

    y_preds: list of lists

    1. Voting
    2. Remove outliers with 60% or more voting

    Don't remove more than 10% of values
    """
    X = pd.read_csv(file_path)

    try:
        rows_to_remove_df = get_final_outliers(y_preds, voting_percentage=voting_percentage, threshold=threshold)

        if rows_to_remove_df.shape[0] > 0:
            X.drop(X.index[rows_to_remove_df['index']], inplace=True)

        treated_file_name = "cleaned_csv_{}.csv".format(experiment_id)
        treated_file_path = os.path.join(media_root, treated_file_name)
        X.to_csv(treated_file_path)

        # Update server
        data = {'experiment_id': experiment_id,
                'treated_file_path': treated_file_name,
                "process_status_id": 3}
        update_server(data)

    except Exception as e:
        print("Error:", e)
        data = {'experiment_id': experiment_id,
                "process_status_id": 4}
        update_server(data)


def get_final_outliers(y_preds, voting_percentage=0.6, threshold=0.1):
    """
    Apply voting and threshold to get rows to remove
    """
    df = pd.DataFrame(y_preds)
    sum_ = df.sum(axis=1, skipna=True)
    nrows = df.shape[0]

    rows_to_remove = []

    for i, v in enumerate(sum_.tolist()):
        if v > voting_percentage * df.shape[1]:
            rows_to_remove.append({"index": i, "confidence": voting_percentage * df.shape[1]})

    rows_to_remove_df = pd.DataFrame(rows_to_remove)
    if rows_to_remove_df.shape[0] > threshold * nrows:
        # Select only 10% rows
        rows_to_remove_df.sort_values('confidence', ascending=False).head((int)(threshold * nrows))

    return rows_to_remove_df


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


def detect_all(file_path, experiment_id, results_path, deleted_features):
    if file_path is None:
        raise Exception("File path is null")

    try:
        delayed_list = []
        for _, space in enumerate(OUTLIER_SPACES):
            delayed_list.append(delayed(detect)(file_path, space, deleted_features))

        results = dask.compute(*delayed_list)
        results = [(r.tolist()) for r in list(results)]
        final_results = dict(zip(range(len(list(results))), results))

        # Store final results

        if not os.path.exists(results_path):
            os.makedirs(results_path)

        file_name = 'detection_results_{}.json'.format(experiment_id)
        results_file_path = os.path.join(results_path, file_name)

        with open(results_file_path, "w") as fp:
            json.dump(final_results, fp)

        # Update server
        data = {'experiment_id':experiment_id,
                'results_file_path': file_name,
                "process_status_id": 3}
        update_server(data)
    except Exception as e:
        print("Error:", e)
        data = {'experiment_id': experiment_id,
                "process_status_id": 4}
        update_server(data)


def update_server(data):
    endpoint = "http://127.0.0.1:8000/app/status/update"
    r = requests.post(url=endpoint, data=data)
    print(r.status_code)


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
