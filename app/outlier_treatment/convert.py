import glob
import os

from scipy.io import loadmat
import pandas as pd
import h5py
import numpy as np

dataset_paths = glob.glob("datasets/*.mat")

print(len(dataset_paths))

for dataset_path in dataset_paths:
    print(dataset_path)

    if dataset_path == "datasets/smtp.mat" or dataset_path == "datasets/http.mat":
        arrays = {}
        f = h5py.File(dataset_path)
        X = None
        y = None
        for k, v in f.items():
            arrays[k] = np.array(v)
            if k == "X":
                X = np.array(v)
            elif k == "y":
                y = np.array(v)

        X = np.swapaxes(X, 0, 1)
        y = np.swapaxes(y, 0, 1)

        try:
            print(X.shape, y.shape)
            df = pd.DataFrame.from_records(X)
            df['label'] = y
            filename, file_extension = os.path.splitext(dataset_path)
            df.to_csv(filename + ".csv", index=False)
        except Exception as e:
            print("Error:", e)
    else:
        try:
            d = loadmat(dataset_path)
            keys = d.keys()
            if "X" in keys and "y" in keys:
                X = d['X']
                y = d['y']

                print(X.shape, y.shape)
                df = pd.DataFrame.from_records(X)
                df['label'] = y
                # print(df)
                filename, file_extension = os.path.splitext(dataset_path)
                df.to_csv(filename+".csv", index=False)
        except Exception as e:
            print("Error:", e)
