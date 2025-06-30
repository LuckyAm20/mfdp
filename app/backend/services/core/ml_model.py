import os
import threading
from abc import ABC, abstractmethod
from typing import Type

import joblib
import numpy as np
import pandas as pd
from joblib import load
from tensorflow.keras.models import load_model


class MLModel(ABC):
    def __init__(self, model, scaler_X, scaler_y):
        self.model = model
        self.scaler_X = scaler_X
        self.scaler_y = scaler_y

    @abstractmethod
    def predict(self, *args, **kwargs):
        pass


class LSTM(MLModel):
    def __init__(self, model_path: str):
        model = load_model(model_path)
        path = os.path.dirname(model_path)
        scaler_X = load(os.path.join(path, 'scaler_X.joblib'))
        scaler_y = load(os.path.join(path, 'scaler_y.joblib'))
        super().__init__(model, scaler_X, scaler_y)

    def predict(self, sequence: np.ndarray) -> np.ndarray:
        batch = sequence[np.newaxis, ...]
        y_pred = self.model.predict(batch)
        return np.squeeze(y_pred, axis=0)

class MLP(MLModel):
    def __init__(self, model_path: str):
        model = joblib.load(model_path)
        path = os.path.dirname(model_path)
        scaler_X = joblib.load(os.path.join(path, 'preprocessor.joblib'))
        super().__init__(model, scaler_X, None)

    def predict(self, seq: pd.DataFrame) -> float:
        x_val = self.scaler_X.transform(seq)
        y_pred = float(self.model.predict(x_val))
        return round(max(0.0, y_pred), 2)

registry: dict[str, tuple[Type[MLModel], str]] = {
    'lstm': (LSTM, 'lstm_v1'),
    'lstmv3': (LSTM, 'lstm_v3'),
    'mlp': (MLP,  'mlp_v1'),
}

class ModelRegistry:
    _lock = threading.Lock()
    _instances: dict[str, object] = {}

    @classmethod
    def get(cls, name: str):
        with cls._lock:
            if name not in cls._instances:
                ModelClass, path_name = registry[name]
                path = cls._model_path(name, path_name)
                cls._instances[name] = ModelClass(path)
            return cls._instances[name]

    @classmethod
    def reload_all(cls):
        with cls._lock:
            for name, (ModelClass, path_name) in registry.items():
                path = cls._model_path(name, path_name)
                cls._instances[name] = ModelClass(path)

    @staticmethod
    def _model_path(name: str, path: str) -> str:
        name = 'lstm' if name.startswith('lstm') else name
        ext = '.keras' if name in ('lstm', 'transformer') else '.joblib'
        return os.path.join('models', path, f'{name}{ext}')
