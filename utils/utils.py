import time
from datetime import datetime


def date_last_post(type_time: str, interval: str, posts_amount: int, schedule_times: list = None):
    """
    Данная функция определяет дату публикации последнего поста при выборке постов из канала - донора.
    :param schedule_times: Список времён для расписания.
    :param posts_amount: Количество постов
    :return: result
    :param type_time: Тип интервала (времени) (минута, час, день)
    :param interval: Интервал (10 мин, 20 мин ...), сам интервал хранится в целочисленном значении
    """
    if interval:  # Проверка на None
        if '🧃' in interval or '🍑' in interval:
            interval = interval[:-1]
    time_now = time.time() + 10800  # gmt + 3 (UnixTime)
    time_result = None
    if type_time.lower() == 'минуты':
        # -1 так как самый первый пост публикуется сразу, без задержек
        time_result = time_now + 60 * int(interval) * (posts_amount - 1)
    elif type_time.lower() == 'часы':
        time_result = time_now + 3600 * int(interval) * (posts_amount - 1)
    elif type_time.lower() == 'дни':
        time_result = time_now + 86400 * int(interval) * (posts_amount - 1)
    elif type_time.lower() == 'arbitrary':  # Произвольный интервал
        result = 'При произвольном интервале время не высчитывается'
        return result
    elif type_time.lower() == 'schedule':  # Интервал с расписанием.
        # result - кол-во дней, которое необходимо будет для публикации всех постов
        result = round(posts_amount/len(schedule_times))
        result_text = f'Осталось {result} дней(-я, -ь) до окончания публикации всех постов'
        return result_text
    result = datetime.utcfromtimestamp(time_result).strftime('%Y-%m-%d %H:%M:%S')
    return result
