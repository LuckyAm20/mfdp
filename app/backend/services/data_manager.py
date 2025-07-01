from datetime import datetime, timedelta
from typing import Optional

import holidays
import numpy as np
import pandas as pd
from meteostat import Hourly, Stations
from sklearn.preprocessing import StandardScaler


class DataManager:
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

    @staticmethod
    def create_feature_vector(location_id: int, date: datetime, hour: int, trips: int) -> pd.DataFrame:
        us_holidays = holidays.US()
        non_working = {
            "New Year's Day", 'MLK Day', "Washington's Birthday", 'Memorial Day',
            'Juneteenth', 'Independence Day', 'Labor Day', 'Thanksgiving', 'Christmas Day'
        }
        df = pd.DataFrame({
            'location_id': [location_id],
            'date': [pd.to_datetime(date)],
            'hour': [hour],
            'trips_count': [trips]
        })

        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_holiday'] = df['date'].apply(lambda d: us_holidays.get(d.date()) in non_working)
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)

        df['is_pre_holiday'] = df['date'].apply(
            lambda d: us_holidays.get((d + timedelta(days=1)).date()) in non_working)
        df['is_post_holiday'] = df['date'].apply(
            lambda d: us_holidays.get((d - timedelta(days=1)).date()) in non_working)

        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

        station = Stations().nearby(40.7128, -74.0060).fetch(1).index[0]

        start_time = pd.Timestamp(year=date.year, month=date.month, day=date.day, hour=hour)
        end_time = start_time + timedelta(hours=1)

        weather_data = Hourly(station, start_time, end_time).fetch()

        if not weather_data.empty:
            row = weather_data.iloc[0]
            df['temp'] = row['temp'] if 'temp' in row and row['temp'] else 0
            df['prcp'] = row['prcp'] if 'prcp' in row and row['prcp'] else 0
            df['wspd'] = row['wspd'] if 'wspd' in row and row['wspd'] else 0
        else:
            df['temp'] = 0
            df['prcp'] = 0
            df['wspd'] = 0

        features = [
            'location_id', 'trips_count', 'hour', 'temp', 'prcp', 'wspd',
            'day_of_week', 'month', 'is_weekend', 'is_holiday',
            'is_month_start', 'is_month_end', 'day_of_year', 'week_of_year',
            'is_pre_holiday', 'is_post_holiday'
        ]

        return pd.DataFrame(df, columns=features)
