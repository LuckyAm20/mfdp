import pandas as pd
from typing import Dict, Any, Tuple
import numpy as np

class DataManager:
    def __init__(self):
        self.datasets: Dict[str, pd.DataFrame] = {}

    def load_csv(self, name: str, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        self.datasets[name] = df
        return df

    def create_sequences(self,
                         df: pd.DataFrame,
                         past_steps: int,
                         future_steps: int
                         ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, dict]:

        ...

    def prepare_data(self, X: np.ndarray, y: np.ndarray, regions: np.ndarray):
        ...

    def save_array(self, arr: np.ndarray, path: str):
        np.save(path, arr)
