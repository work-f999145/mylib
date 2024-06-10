def process_structure(data):
    """
    Обрезание списков json файла до первого элемента
    """
    if isinstance(data, dict):
        # Если это словарь, рекурсивно пройтись по его значениям
        return {k: process_structure(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Если это список, взять только первый элемент и обработать его
        return [process_structure(data[0])] if data else []
    else:
        # Если это ни словарь, ни список, вернуть значение как есть
        return data