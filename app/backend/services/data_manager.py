from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class DataManager:
    # Класс-переменные для кеша
    _df: Optional[pd.DataFrame] = None
    _loaded_path: Optional[str] = None

    def __init__(self, path: Optional[str] = None):
        self._path: Optional[str] = path
        self.load_csv()

    @property
    def path(self) -> Optional[str]:
        return self._path

    @path.setter
    def path(self, new_path: str):
        if new_path != self._path:
            DataManager._df = None
            DataManager._loaded_path = None
            self._path = new_path
            self.load_csv()

    def load_csv(self) -> pd.DataFrame:
        if DataManager._df is None or DataManager._loaded_path != self.path:
            DataManager._df = pd.read_csv(self.path)
            DataManager._loaded_path = self.path
        return DataManager._df

    @staticmethod
    def create_single_sequence(
            target_datetime: datetime,
            district_id: int,
            scaler_X: StandardScaler,
            past_steps: int = 72,
            date_col: str = 'date',
            hour_col: str = 'hour'
    ) -> tuple[np.ndarray, np.ndarray]:
        features_cols = [
            'trips_count', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
            'is_holiday', 'month', 'is_weekend', 'is_month_start', 'is_month_end',
            'day_of_year', 'week_of_year', 'is_pre_holiday', 'is_post_holiday',
            'lag_1h', 'lag_24h', 'lag_168h', 'roll_168h_mean', 'roll_168h_median', 'roll_168h_std',
            'time_idx', 'temp', 'prcp', 'wspd'
        ]

        df = DataManager._df

        sub = df[df['location_id'] == district_id].copy()
        if sub.empty:
            raise ValueError(f'Нет данных для района={district_id}')

        sub['__date__'] = pd.to_datetime(sub[date_col]).dt.normalize()
        sub['ts'] = sub['__date__'] + pd.to_timedelta(sub[hour_col], unit='h')
        sub.drop(columns=['__date__'], inplace=True)

        sub = sub.sort_values('ts').reset_index(drop=True)

        le_mask = sub['ts'] <= target_datetime
        if not le_mask.any():
            raise ValueError(f'В районе={district_id} нет записей ≤ {target_datetime}')
        idx = sub[le_mask].index[-1]

        available = idx + 1

        hist = sub.iloc[0:idx + 1].copy()

        full_feats = sub[features_cols].astype('float32').to_numpy()
        means = np.nanmean(full_feats, axis=0)

        X_hist = hist[features_cols].astype('float32').to_numpy()

        mask_hist_nan = np.isnan(X_hist)
        if mask_hist_nan.any():
            X_hist[mask_hist_nan] = np.take(means, np.where(mask_hist_nan)[1])

        if available < past_steps:
            pad_count = past_steps - available

            pad_block = np.tile(means, (pad_count, 1))

            X_window = np.vstack([pad_block, X_hist])
        else:
            X_window = X_hist[-past_steps:]

        seq_scaled = scaler_X.transform(X_window)

        return seq_scaled
