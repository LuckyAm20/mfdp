from typing import Type

import numpy as np
from abc import ABC, abstractmethod
from tensorflow.keras.models import load_model
import threading
import os

class MLModel(ABC):
    def __init__(self, model):
        self.model = model

    @abstractmethod
    def predict(self, *args, **kwargs):
        pass


class LSTM(MLModel):
    def __init__(self, model_path: str):
        model = load_model(model_path)
        super().__init__(model)

    def predict(self, sequence: np.ndarray) -> np.ndarray:
        batch = sequence[np.newaxis, ...]
        y_pred = self.model.predict(batch)
        return np.squeeze(y_pred, axis=0)


registry: dict[str, Type[MLModel]] = {
    'lstm': LSTM,
}

# def load_model_by_name(name: str) -> MLModel:
#     if name not in registry:
#         raise ValueError(f'Model "{name}" is not registered. '
#                          f'Available: {list(registry)}')
#
#     ModelClass = registry[name]
#     if issubclass(ModelClass, LSTM):
#         filename = f'models/{name}.keras'
#         return ModelClass(filename)


class ModelRegistry:
    _lock = threading.Lock()
    _instances: dict[str, object] = {}

    @classmethod
    def get(cls, name: str):
        with cls._lock:
            if name not in cls._instances:
                ModelClass = registry[name]
                path = cls._model_path(name)
                cls._instances[name] = ModelClass(path)
            return cls._instances[name]

    @classmethod
    def reload_all(cls):
        with cls._lock:
            for name, ModelClass in registry.items():
                path = cls._model_path(name)
                cls._instances[name] = ModelClass(path)

    @staticmethod
    def _model_path(name: str) -> str:
        ext = '.keras' if name in ('lstm', 'transformer') else '.pth'
        return os.path.join('models', f'{name}{ext}')
