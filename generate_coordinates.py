import pandas as pd
from pathlib import Path
from typing import NamedTuple
import numpy as np
import warnings
from sklearn.cluster import KMeans


class Coordinates(NamedTuple):
    lat: float
    long: float



def class_type(d:pd.Series):
    match d['pop']:
        case x if x < 0.2:
            return 'A'
        case x if x < 0.4:
            return 'B'
        case x if x < 0.6:
            return 'C'
        case x if x < 0.8:
            return 'D'
        case _:
            return 'E'



def generate_random_points(origin: Coordinates, n, radius):
    # Преобразуем географические координаты начальной точки в радианы
    origin_lat_rad = np.radians(origin.lat)
    origin_lon_rad = np.radians(origin.long)

    # Генерируем случайные углы и радиусы для создания точек
    random_angles = np.random.uniform(0, 2*np.pi, n)
    random_radius = np.random.uniform(0, radius, n)

    # Рассчитываем географические координаты случайных точек
    random_latitudes = np.degrees(np.arcsin(np.sin(origin_lat_rad) * np.cos(random_radius / 6371) +
                                             np.cos(origin_lat_rad) * np.sin(random_radius / 6371) * np.cos(random_angles)))
    random_longitudes = np.degrees(origin_lon_rad + np.arctan2(np.sin(random_angles) * np.sin(random_radius / 6371) * np.cos(origin_lat_rad),
                                                               np.cos(random_radius / 6371) - np.sin(origin_lat_rad) * np.sin(np.radians(random_latitudes))))

    return list(map(lambda x: Coordinates(*x), zip(random_latitudes, random_longitudes)))




def get_list_logg_lst_claster(input_df: pd.DataFrame, cols_name: list[str, str], num_points_to_select: int, random_state: int|None = None):
    """
    Функция принимает датасет с координатами,
    кластеризирует его на n-кластеров,
    находит ближайшие координаты к центру кластера,
    и выводит датасет с отфильтрованными координатами
    """
    with warnings.catch_warnings(action="ignore"):
        kmeans = KMeans(n_clusters=num_points_to_select, random_state=random_state)
        input_df['cluster'] = kmeans.fit_predict(input_df[cols_name])

    # Выбираем центры кластеров
    cluster_centers = pd.DataFrame(kmeans.cluster_centers_, columns=cols_name)

    # Выводим результат
    selected_points = cluster_centers[cols_name]

    # Для каждого кластера выбираем ближайшие к центру точки
    selected_points = []
    for cluster_id in range(num_points_to_select):
        cluster_points = input_df[input_df['cluster'] == cluster_id]
        distance_to_center = ((cluster_points[cols_name] - cluster_centers.loc[cluster_id])**2).sum(axis=1)
        closest_points = input_df.loc[distance_to_center.idxmin()]
        selected_points.append(closest_points)

    return pd.DataFrame(selected_points)





def get_cord() -> pd.DataFrame:
    
    p_dictionaries = Path('data','dictionaries')


    sity_df = (pd.read_parquet(p_dictionaries.joinpath('city.parquet'))
                .sort_values('population', ascending=False, ignore_index=True)
                .assign(pop = lambda x: x['population'].cumsum()/x['population'].sum())
                .assign(pop = lambda x: x.apply(class_type, axis=1))
                .reindex(columns=[
                                'fias_id',
                                'geo_lat',
                                'geo_lon',
                                'pop',
                                # 'radius'
                                ])
                )

    out_list = []
    for Index, fias_id, geo_lat, geo_lon, pop in list(sity_df.itertuples()):
        match pop:
            case 'A':
                out_list.append(
                    get_list_logg_lst_claster(pd.DataFrame(generate_random_points(Coordinates(geo_lat, geo_lon), n=80*30, radius=15)).assign(fias_id = fias_id), 
                                                ['lat', 'long'],
                                                num_points_to_select=30
                                                )
                        )
            case 'B':
                out_list.append(
                    get_list_logg_lst_claster(pd.DataFrame(generate_random_points(Coordinates(geo_lat, geo_lon), n=80*8, radius=10)).assign(fias_id = fias_id), 
                                                ['lat', 'long'],
                                                num_points_to_select=8
                                                )
                        )
            case 'C':
                out_list.append(
                    get_list_logg_lst_claster(pd.DataFrame(generate_random_points(Coordinates(geo_lat, geo_lon), n=80*5, radius=8)).assign(fias_id = fias_id), 
                                                ['lat', 'long'],
                                                num_points_to_select=5
                                                )
                        )
            case 'D':
                out_list.append(
                    get_list_logg_lst_claster(pd.DataFrame(generate_random_points(Coordinates(geo_lat, geo_lon), n=80*3, radius=5)).assign(fias_id = fias_id), 
                                                ['lat', 'long'],
                                                num_points_to_select=3
                                                )
                        )
            case 'E':
                out_list.append(
                    get_list_logg_lst_claster(pd.DataFrame(generate_random_points(Coordinates(geo_lat, geo_lon), n=50, radius=3)).assign(fias_id = fias_id), 
                                                ['lat', 'long'],
                                                num_points_to_select=1
                                                )
                        )

    return pd.concat(out_list, ignore_index=True).drop(columns='cluster')