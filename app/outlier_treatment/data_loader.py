import filetype
import pandas as pd
from pathlib import Path


class DataLoader(object):
    @staticmethod
    def load(file_path):
        suffix = Path(file_path).suffix
        # file_type = filetype.guess(file_path)

        if 'csv' in suffix:
            df = pd.read_csv(file_path)
        elif 'xls' in suffix:
            df = pd.read_excel(file_path)
        elif 'h5' in suffix or 'hdf' in suffix:
            df = pd.read_hdf(file_path, encoding="utf-8")
        else:
            print("Invalid file")
            df = None

        return df
