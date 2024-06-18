from pathlib import Path
import pandas as pd
from datetime import datetime
from typing import NamedTuple
import pyarrow.parquet as pq
from pathlib import Path
import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output
import json
from pydantic import BaseModel, ValidationError
from typing import Callable


class Coordinates(NamedTuple):
    lat: float
    long: float

# Декоратор для валидации аргументов функции
def validate_args(model: BaseModel):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                # Валидация аргументов с использованием модели
                validated_args: BaseModel = model(**kwargs)
            except ValidationError as e:
                return e
            return func(*args, **validated_args.model_dump())
        return wrapper
    return decorator




def json_encode(df_: pd.DataFrame):
    def my_json_encode(x):
        if isinstance(x, (tuple, list)):
            return json.dumps(x, ensure_ascii=False)
        else:
            return 'null'
    
    for col in df_.select_dtypes('object').columns:
        df_[col] = df_[col].apply(my_json_encode).astype('string')
    
    return df_



def separation_frame_row(input_df: pd.DataFrame, rows: int=500) -> list[pd.DataFrame]:
    """
        Функция для дробления DataFrame.
        rows: количество строк, по сколько строк будет делится DataFrame
    """
    out_list = list()
    for index in range(0, input_df.shape[0], rows):
        out_list.append(input_df.iloc[index:index+rows].reset_index())
    return out_list


def _save_df_to_excel(df_:pd.DataFrame, name: str, folder: Path):
    with pd.ExcelWriter(
                    folder.joinpath(f'{name}.xlsx'),
                    engine='xlsxwriter',
                    engine_kwargs={'options': {'strings_to_urls': False}}
                    ) as writer:
        df_.to_excel(writer, index=False)



# Функция для сохранения и создания копии.
def _save_df_to_parquet(df_: pd.DataFrame, archive_name: str = 'no_name', folder:Path = Path('data'), replace: bool=False) -> None:
    """
        Функция позволяет сохранять pd.DataFrame в формате parquet,
        при это создавая бекап старой версии.

        df_: сохраняемый дтафрейм
        archive_name: имя архива и по совместитеству имя файла
        folder: папка, куда поместится файл (по умолчанию 'data')
        replace: заменить ли предыдущий файл(по умолчанию - False)
    """
    
    folder.mkdir(exist_ok=True)
    file_path = folder.joinpath(archive_name + '.parquet')
    
    # Проверяем, существует ли файл
    if file_path.exists() and not replace:
        # Получаем время создания файла
        time = datetime.fromtimestamp(file_path.lstat().st_mtime).strftime('%Y-%m-%d %H-%M-%S')

        # Создаем новое имя файла с добавлением времени Unix
        new_file_name = file_path.stem + " " + str(time) + file_path.suffix

        # Создаем новый путь для переименованного файла
        new_file_path = file_path.with_name(new_file_name)
        # Переименовываем файл
        file_path.rename(new_file_path)

    # to parquet
    file = folder.joinpath(archive_name + '.parquet')
    try:
        pq.write_table(pq.read_pandas(df_), file, compression='ZSTD')
    except Exception:
        df_.to_parquet(file, engine='pyarrow', compression='zstd')



def pd_series_dict(df:pd.DataFrame, col: str, prefix: str|None = None, suffix: str = ' 1', col_names: list|dict|None = None):
    df.columns = df.columns.astype(str)
    try:
        tmp = pd.json_normalize(df[col])
    except KeyError:
        print(f'Not key: "{col}"')
        return df
    
    tmp.columns = tmp.columns.astype(str)

    if prefix:
        tmp = tmp.rename(columns=lambda x: str(prefix) + x)
    else:
        if col_names:
            if type(col_names) is dict:
                tmp = tmp.rename(columns=col_names)
            elif type(col_names) is list:
                tmp.columns = col_names

    col_inter = set(df.drop(columns=col).columns).intersection(set(tmp.columns))
    col_inter = dict(map(lambda x: (x, x + suffix), col_inter))
    tmp = tmp.rename(columns=col_inter)
    return pd.concat((df.drop(columns=col), tmp), axis=1)



# Рекурсивная функция для создания вложенного словаря
def build_nested_dict(data: dict) -> dict:
    def insert(d, keys, value):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]  # Если keys не список или кортеж, преобразуем его в список
        
        key = keys[0]
        if len(keys) == 1:
            if pd.notna(value) and value != 0:  # Удаление NaN и нулевых значений
                d[key] = value
        else:
            if key not in d:
                d[key] = {}
            insert(d[key], keys[1:], value)
            if not d[key]:  # Удаление пустых словарей
                del d[key]
    
    nested_dict = {}
    for keys, value in data.items():
        insert(nested_dict, keys, value)
    
    return nested_dict

























# EXPORT TO EXCEL

def export_to_excel():
    p_folders = Path('data')
    file_list, file_list_n = ['', '']
    index_file = 0
    dir_list = list(p_folders.iterdir())
    dir_list_names = list(map(lambda x: x.stem, dir_list))

    tog_buttom = widgets.ToggleButtons(
                                            options=dir_list_names,
                                            disabled=False,
                                            button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                            tooltips=['Description of slow', 'Description of regular', 'Description of fast'],

                                        )
    
    dropdown = widgets.Dropdown(
                                            options=[('',0)],
                                            # value=0,
                                            description='Number:',
                                            disabled=False,
                                        )
    
    
    def get_files_list(item):
        nonlocal p_folders, file_list, file_list_n, dropdown, grid, out2
        file_list = list(filter(lambda x: x.suffix == '.parquet', p_folders.joinpath(item).iterdir()))
        file_list_n = list(map(lambda x: x[::-1], enumerate(map(lambda x: x.stem, file_list))))
        
        def index_file_connection(item):
            display(item)

        
        # Функция для отображения данных с учетом выбранных фильтров
        def display_filtered_data(dropdown_int: int, on_print_value: bool):
            nonlocal file_list, index_file, out2, on_print
            if not index_file == dropdown_int:
                on_print.value = False
                out2.clear_output()
                index_file = dropdown_int
            elif on_print_value:
                out2.clear_output()
                return_data = file_list[dropdown_int]
                df = pd.read_parquet(return_data)
                out_df = df.head()
                out2.append_display_data(out_df)
                index_file == dropdown_int
            else:
                out2.clear_output()
        
        def get_shape(dropdown: int):
            nonlocal file_list
            return_data = file_list[dropdown]
            df = pq.ParquetFile(return_data)
            display(f'Размерность: {df.metadata.num_rows}x{df.metadata.num_columns}')

        def save_file(t):
            nonlocal dropdown, file_list, name_file
            start = datetime.now()
            print(f'Сохранение {name_file.value}.xlsx', end=': ')
            df = pd.read_parquet(file_list[dropdown.value])
            _save_df_to_excel(df, name_file.value, Path('data', 'excel'))
            print('выполнено за', str((datetime.now() - start)))


        if file_list_n:

            dropdown = widgets.Dropdown(
                                            options=file_list_n,
                                            value=0,
                                            description='File:',
                                            disabled=False,
                                            layout=widgets.Layout(width='70%'),
                                        )
            
            name_file = widgets.Text(
                                            value='something',
                                            placeholder='Name File',
                                            description='Name excel:',
                                            disabled=False   
                                        )
            
            on_print = widgets.Checkbox(
                                            value=False,
                                            description='Показать 5 строк',
                                            disabled=False,
                                            button_style='info', # 'success', 'info', 'warning', 'danger' or ''
                                            tooltip='Description',
                                        )

            export = widgets.Button(
                                    # value=False,
                                    description='export',
                                    disabled=False,
                                    button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                    tooltip='Description',
                                )
            


            ot = widgets.interactive_output(index_file_connection, {'item': dropdown})
            output = widgets.interactive_output(display_filtered_data, {'dropdown_int': dropdown, 'on_print_value': on_print})
            info_shape = widgets.interactive_output(get_shape, {'dropdown': dropdown})
            export.on_click(save_file)
            
            
            grid[0, 0:2] = dropdown
            grid[1, 0] = info_shape
            grid[1, 1] = on_print
            grid[0, 2] = name_file
            grid[1, 2] = export


        else:
            dropdown = widgets.Dropdown(
                                            options=[('',0)],
                                            value=0,
                                            description='Number:',
                                            disabled=True,
                                            layout=widgets.Layout(width='70%'),
                                        )
            
            name_file = widgets.Text(
                                            value='something',
                                            placeholder='Name File',
                                            description='Name excel:',
                                            disabled=True   
                                        )
            
            on_print = widgets.Checkbox(
                                            value=False,
                                            description='Показать 5 строк',
                                            disabled=True,
                                            button_style='info', # 'success', 'info', 'warning', 'danger' or ''
                                            tooltip='Description',
                                        )
            
            export = widgets.Button(
                                    description='export',
                                    disabled=True,
                                    button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                    tooltip='Description',
                                )
            
            
            ot = widgets.HTML('нет parquet файлов')
            output = widgets.interactive_output(display_filtered_data, {'dropdown': dropdown, 'on_print': on_print})
            
            
            
            grid[0, 0:2] = dropdown
            grid[1, 0] = ot
            grid[1, 1] = on_print
            grid[0, 2] = name_file
            grid[1, 2] = export

            out2.clear_output()

            return grid

        
    grid = widgets.GridspecLayout(2, 4, height='100px')
    
    out2 = widgets.Output()

    get_files_list('dictionaries')
    # interactive
    widgets.interactive_output(get_files_list, {'item': tog_buttom})


    display(tog_buttom, grid, out2)
    
