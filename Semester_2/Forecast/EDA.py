import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import seaborn as sns
import matplotlib.pyplot as plt
# from ydata_profiling import ProfileReport
import holidays
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder

# 1. Загрузка данных
def load_data():
    sales = pd.read_csv('data/train.csv', parse_dates=['date'])
    weather = pd.read_csv('data/weather.csv', parse_dates=['date'])
    key = pd.read_csv('data/key.csv')
    data = (
        sales
          .merge(key,     on='store_nbr')
          .merge(weather, on=['station_nbr','date'])
    )
    # Сохраняем в файл
    data.to_csv('data/merged_data.csv', index=False)

    return data

# Создание отчёта
def create_report(data):
    profile = ProfileReport(data, title='Pandas Profiling Report', explorative=True)
    profile.to_file("weather6.html")

# Загрузка данных из файла
# список бинарных колонок, которые могут принимать только 0 или 1
BINARY_COLS = [
    'BCFG','BLDU','BLSN','BR','DU','DZ','FG','FG+','FU','FZDZ','FZFG',
    'FZRA','GR','GS','HZ','MIFG','PL','PRFG','RA','SG','SN','SQ','TS',
    'TSRA','TSSN','UP','VCFG','VCTS'
]
def load_data_from_file(path: str) -> pd.DataFrame:
    """Загрузить CSV и привести date к datetime."""
    dtype_spec = {col: 'uint8' for col in BINARY_COLS}
    df = pd.read_csv(path, dtype=dtype_spec, low_memory=False)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    return df


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Заменить метки:
      - 'M' или 'm' → NaN (пропущенные),
      - 'T' или 't' → 0 (trace-показатели осадков)
    и сконвертировать в float/int.
    """
    # глобальные замены
    df = df.replace({'M': np.nan, 'm': np.nan, 'T': 0, 't': 0})

    # список всех столбцов, которые нужно конвертнуть
    numeric_cols = [
        'store_nbr', 'item_nbr', 'units', 'station_nbr',
        'tmax', 'tmin', 'tavg', 'depart', 'dewpoint', 'wetbulb',
        'heat', 'cool', 'snowfall', 'preciptotal',
        'stnpressure', 'sealevel', 'resultspeed', 'resultdir', 'avgspeed'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def convert_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Преобразовать столбцы sunrise/sunset из HHMM-строк в целое число HHMM.
    '-' → NaN, затем to_numeric.
    """
    for col in ['sunrise', 'sunset']:
        df[col] = df[col].replace('-', np.nan)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Заполнить пропуски:
      - для числовых столбцов — 0,
      - если потребуется, можно расширить логику для специальных столбцов.
    """
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        # mean_val = df[col].mean()
        df[col] = df[col].fillna(0)
    return df

# Заполняем нули в столбцах tavg, tmax, tmin средним значением по станции и по ближайшим ненулевым значениям на даты до и после
def fill_temperature_zeros(df):
    """Заполнение нулевых tavg, tmax, tmin по станции и интерполяцией."""
    df = df.copy()
    df = df.sort_values(['station_nbr', 'date'])
    for col in ['tavg', 'tmax', 'tmin']:
        # заменяем нули на NaN
        df[col] = df[col].replace(0, np.nan)
        # интерполируем линейно между ближайшими датами
        df[col] = df.groupby('station_nbr')[col].transform(
            lambda x: x.interpolate(method='linear', limit_direction='both')
        )
        # оставшиеся NaN заполняем средним по станции
        df[col] = df.groupby('station_nbr')[col].transform(
            lambda x: x.fillna(x.mean())
        )
    return df


def encode_codesum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Разбить codesum на бинарные признаки для каждого уникального кода.
    """
    # получаем «one‑hot» по пробелу
    dummies = df['codesum'].fillna('').str.get_dummies(sep=' ')
    # если вдруг появилась колонка '' — удаляем
    if '' in dummies.columns:
        dummies.drop(columns=[''], inplace=True)
    df = pd.concat([df, dummies], axis=1)
    df.drop(columns=['codesum'], inplace=True)
    return df


def preprocess(path: str) -> pd.DataFrame:
    """Вся цепочка предобработки данных."""
    df = load_data_from_file('data/merged_data.csv')
    df = convert_numeric_columns(df)
    df = convert_time_columns(df)
    df = fill_missing(df)
    df = encode_codesum(df)
    return df


def add_time_features(df):
    """Генерация временных признаков на основе даты."""
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    df['season'] = df['month'].map({12: 'winter', 1: 'winter', 2: 'winter',
                                    3: 'spring', 4: 'spring', 5: 'spring',
                                    6: 'summer', 7: 'summer', 8: 'summer',
                                    9: 'autumn', 10: 'autumn', 11: 'autumn'})
    
    df['day_of_year'] = df['date'].dt.dayofyear

    return df


def add_weather_features(df):
    """Генерация погодных признаков."""
    df['temperature_diff'] = df['tmax'] - df['tmin']
    df['heavy_precipitation'] = (df['preciptotal'].fillna(0).astype(float) > 0.5).astype(int)

    # Комфортный индекс
    df['comfort_index'] = df['tavg'] - 0.55 * (1 - (df['dewpoint'] / 100)) * (df['tavg'] - 58) - 0.35 * df['avgspeed']
    return df


def add_sales_features(df):
    """Признаки, связанные с магазином и товаром."""
    df['avg_daily_sales_item'] = df.groupby(['store_nbr', 'item_nbr'])['units'].transform('mean')

    store_sales = df.groupby('store_nbr')['units'].sum()
    df['store_sales_rank'] = df['store_nbr'].map(store_sales.rank(method='dense', ascending=False))

    item_sales = df.groupby('item_nbr')['units'].sum()
    df['item_sales_rank'] = df['item_nbr'].map(item_sales.rank(method='dense', ascending=False))
    return df


def add_rolling_weather_features(df):
    """Добавление признаков на основе средних значений за предыдущие 3 дня."""
    df = df.sort_values(by=['station_nbr', 'date'])
    df['avg_temp_last_3_days'] = df.groupby('station_nbr')['tavg'].transform(
        lambda x: x.shift(1).rolling(window=3).mean())
    df['avg_precip_last_3_days'] = df.groupby('station_nbr')['preciptotal'].transform(
        lambda x: x.shift(1).rolling(window=3).mean())
    return df


def add_days_since_start(df):
    """Добавление нумерации дней относительно самой ранней даты в датасете."""
    min_date = df['date'].min()
    df['days_since_start'] = (df['date'] - min_date).dt.days
    return df

def add_holiday_feature(df):
    """Является ли день праздничным в США в период 2012-2014."""
    us_holidays = holidays.US(years=[2012, 2013, 2014])
    df['is_holiday'] = df['date'].isin(us_holidays).astype(int)
    return df


def add_features(df):
    """Объединение всех этапов добавления признаков, кроме продаж."""
    df = add_time_features(df)
    df = add_weather_features(df)
    df = add_rolling_weather_features(df)
    df = add_days_since_start(df)
    df = add_holiday_feature(df)
    return df


def remove_zero_sales(df):
    """Удаление товаров, которые никогда не продавались в конкретных магазинах."""
    sales_sum = df.groupby(['store_nbr', 'item_nbr'])['units'].sum()
    zero_sales = sales_sum[sales_sum == 0].index
    df_clean = df[~df.set_index(['store_nbr', 'item_nbr']).index.isin(zero_sales)].copy()
    return df_clean


def combine_sunset_sunrise(df):
    """Создание признака 'daylight_duration' (продолжительность светового дня)."""
    df = df.copy()
    df['daylight_duration'] = df['sunset'] - df['sunrise']
    df = df.drop(['sunrise', 'sunset'], axis=1)
    return df

def drop_highly_correlated_features(df):
    """Удаление высоко скоррелированных признаков."""
    drop_cols = [
        'resultspeed',  # сильно коррелирует с avgspeed
        'tmax', 'tmin',  # сильно коррелируют с tavg
        'dewpoint', 'wetbulb',  # сильно коррелируют с tavg
        'heat', 'cool',  # сильно коррелируют с tavg
        'sealevel',  # сильно коррелирует с stnpressure
    ]
    df = df.drop(columns=drop_cols)
    return df

def fill_missing_values(df):
    """Заполнение пропусков подходящими значениями."""
    df = df.copy()
    # snowfall и preciptotal — нулями
    df['snowfall'] = df['snowfall'].fillna(0)
    df['preciptotal'] = df['preciptotal'].fillna(0)

    # depart — медианой
    median_depart = df['depart'].median()
    df['depart'] = df['depart'].fillna(median_depart)

    # stnpressure — средним
    mean_pressure = df['stnpressure'].mean()
    df['stnpressure'] = df['stnpressure'].fillna(mean_pressure)

    # tavg — средним по станции и месяцу
    df['month'] = df['date'].dt.month
    df['tavg'] = df.groupby(['station_nbr', 'month'])['tavg'].transform(lambda x: x.fillna(x.mean()))

    # daylight_duration — средним
    mean_daylight = df['daylight_duration'].mean()
    df['daylight_duration'] = df['daylight_duration'].fillna(mean_daylight)

    # avgspeed — средним
    mean_speed = df['avgspeed'].mean()
    df['avgspeed'] = df['avgspeed'].fillna(mean_speed)

    return df

def remove_rare_weather_events(df):
    """Удаление бинарных признаков погодных явлений, которые встречаются менее 1% времени."""
    binary_weather_cols = [
        'BCFG','BLDU','BLSN','BR','DU','DZ','FG','FG+','FU','FZDZ','FZFG',
        'FZRA','GR','GS','HZ','MIFG','PL','PRFG','RA','SG','SN','SQ',
        'TS','TSRA','TSSN','UP','VCFG','VCTS'
    ]
    rare_cols = [col for col in binary_weather_cols if df[col].mean() < 0.01]
    df = df.drop(columns=rare_cols)
    return df


# Итоговая функция, которая проводит все шаги очистки
def clean_data(df):
    # df = remove_zero_sales(df)
    df = combine_sunset_sunrise(df)
    df = drop_highly_correlated_features(df)
    df = fill_missing_values(df)
    df = remove_rare_weather_events(df)
    return df

# Функция для заполнения daylight_duration средним между ближайшими не нулевыми значениями
def fill_daylight_duration(df):
    df = df.sort_values('date')
    df['daylight_duration'] = df['daylight_duration'].replace(0, np.nan)
    df['daylight_duration'] = df['daylight_duration'].interpolate(method='linear', limit_direction='both')
    return df

# Перевод признака season в числовой формат
def encode_season(df):
    season_mapping = {'winter': 1, 'spring': 2, 'summer': 3, 'autumn': 4}
    df['season_encoded'] = df['season'].map(season_mapping)
    df.drop('season', axis=1, inplace=True)
    return df

# Удаление сильно скоррелированных признаков
def remove_highly_correlated(df):
    cols_to_remove = [
        'avg_daily_sales_item',  # корреляция с item_nbr и item_sales_rank
        'avg_precip_last_3_days',  # корреляция с preciptotal и heavy_precipitation
        'avg_temp_last_3_days',  # корреляция с comfort_index и tavg
        'day_of_week',  # корреляция с weekend
        'stnpressure'  # корреляция с store_sales_rank
    ]
    df.drop(cols_to_remove, axis=1, inplace=True)
    return df

# Общая функция для улучшения датасета
def data_clean2(df):
    df = fill_daylight_duration(df)
    df = encode_season(df)
    # df = remove_highly_correlated(df) # Пока не удаляем сильно скоррелированные признаки
    return df

def add_cyclical_feature(df, col, period):
    radians = 2 * np.pi * df[col] / period
    df[f"{col}_sin"] = np.sin(radians)
    df[f"{col}_cos"] = np.cos(radians)
    return df

if __name__ == '__main__':
    data = load_data()
    # create_report(data)
    df = preprocess('data/merged_data.csv')
    df = fill_temperature_zeros(df)
    df = add_features(df)
    df = remove_zero_sales(df) # Осталось 5% от данных 236038
    df = add_sales_features(df)
    df = clean_data(df)
    df = data_clean2(df)


    # 'season' (1–4), 'weekday' (0–6), 'month' (1–12)
    df = add_cyclical_feature(df, "day_of_year", 365.25)
    df = add_cyclical_feature(df, "season_encoded", 4)
    df = add_cyclical_feature(df, "day_of_week", 7)
    df = add_cyclical_feature(df, "month", 12)
    df = df.drop(columns=["day_of_year", "season_encoded", "day_of_week", "month"])
    
    df.to_csv('data/cleaned_data.csv', index=False)
    
    features_to_scale = [
                'tavg',
                'depart',
                'snowfall',
                'preciptotal',
                'stnpressure',
                'resultdir',
                'avgspeed',
                'temperature_diff',
                'comfort_index',
                'avg_temp_last_3_days',
                'avg_precip_last_3_days',
                'days_since_start',
                'avg_daily_sales_item',
                'store_sales_rank',
                'item_sales_rank',
                'daylight_duration']
    
    df_scaled = df.copy()
    scaler = MinMaxScaler(feature_range=(-1, 1))
    df_scaled[features_to_scale] = scaler.fit_transform(df_scaled[features_to_scale])
    df_scaled['unique_id'] = df_scaled['store_nbr'].astype(str) + '_' + df_scaled['item_nbr'].astype(str)
    df_scaled = df_scaled.drop(columns=['store_nbr', 'item_nbr'])

    enc = OneHotEncoder(sparse_output=False, dtype=int, handle_unknown='ignore')
    ohe_array = enc.fit_transform(df_scaled[['station_nbr']])
    ohe_cols = enc.get_feature_names_out(['station_nbr'])

    df_ohe = pd.concat([
        df_scaled.drop('station_nbr', axis=1),
        pd.DataFrame(ohe_array, columns=ohe_cols, index=df_scaled.index)
    ], axis=1)

    print(df_ohe)

    
    df_ohe.to_csv('data/data_for_modeling.csv', index=False)
    
    # create_report(df)


