from typing import Type

import numpy as np
from abc import ABC, abstractmethod
from tensorflow.keras.models import load_model


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

def load_model_by_name(name: str) -> MLModel:
    if name not in registry:
        raise ValueError(f'Model "{name}" is not registered. '
                         f'Available: {list(registry)}')

    ModelClass = registry[name]
    if issubclass(ModelClass, LSTM):
        filename = f'models/{name}.keras'
        return ModelClass(filename)
