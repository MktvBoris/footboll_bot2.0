import datetime
from typing import Dict, Union

from loguru import logger

from config_data.config import ATTACKS, DANGEROUS_ATTACKS, SHOTS_ON_TARGET, SHOTS_TOWARDS_THE_GOAL, ID_CHAT, \
    PARTNERS_URL, CORNERS, OUT_LIST, CHECK_RED_CARDS
from datadase.count_table import get_countlist, add_countlist
from datadase.dumplist_table import add_dumplist, check_dumplist
from datadase.sentlist_table import add_sentlist, check_sentlist
from datadase.statlist_table import get_statlist
from loader_telebot import bot
from utilities.other import get_request


@logger.catch
def connect_to_match(id_match):
    """
    Функция возвращает json данные матча
    """
    url = 'https://1xstavka.ru/LiveFeed/GetGameZip?'
    params = {
        "id": id_match, "lng": 'ru',
        'GroupEvents': 'true',
        'grMode': 2,
    }
    response_match = get_request(url, params=params)
    if response_match is not None and response_match.status_code == 200:
        return response_match.json()
    else:
        return False


@logger.catch
def is_there_total(data_match):
    """
    Функция возвращает котировки на тотал больше матча
    """
    for data in data_match:
        try:
            if data['G'] == 4:
                find_data = f"<b>ТБ</b> {data['E'][0][0]['P']} - {data['E'][0][0]['C']}"
                if len(data['E'][0]) > 1:
                    find_data += f", {data['E'][0][1]['P']} - {data['E'][0][1]['C']}"
                return find_data
        except (KeyError, TypeError):
            logger.info("Нет ключа в котировке")
            return False


@logger.catch
def add_stats(data_match) -> Union[Dict, bool]:
    """
    Функция возвращает статистику матча
    """
    stats = {}
    for index in data_match:
        try:
            if index['ID'] == 45:  # Атаки
                stats['Атаки'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 58:  # Опасные атаки
                stats['Опасные атаки'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 29:  # Владение мячом
                stats['Владение мячом'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 59:  # Удары в створ
                stats['Удары в створ'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 60:  # Удары в сторону ворот
                stats['Удары в сторону ворот'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 70:  # Угловые
                stats['Угловые'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 26:  # Желтые карточки
                stats['Желтые карточки'] = [int(index['S1']), int(index['S2'])]
            elif index['ID'] == 71:  # Красные карточки
                stats['Красные карточки'] = [int(index['S1']), int(index['S2'])]
        except (KeyError, TypeError):
            logger.info("Нет ключа в статистике")
            return False
    return stats


@logger.catch
def filter_events(stats) -> bool:
    """
    Функция отбирает мачт по наличию карточек
    """
    if stats.get('Красные карточки'):
        return sum(stats['Красные карточки']) > 0


@logger.catch
def filter_stats(stats) -> bool:
    """
    Функция отбирает матч по статистике
    """
    # Проверяем по нужным критериям
    flag = True
    for key, value in stats.items():
        if key == 'Атаки':
            if value[0] + value[1] < ATTACKS:
                flag = False
        elif key == 'Опасные атаки':
            if value[0] + value[1] < DANGEROUS_ATTACKS:
                flag = False
        elif key == 'Удары в створ':
            if value[0] + value[1] < SHOTS_ON_TARGET:
                flag = False
        elif key == 'Удары в сторону ворот':
            if value[0] + value[1] < SHOTS_TOWARDS_THE_GOAL:
                flag = False
        elif key == 'Угловые':
            if value[0] + value[1] < CORNERS:
                flag = False

    return flag


@logger.catch
def get_statistic(liga) -> str:
    """
    Функция получает статистику по чемпионату
    """
    liga_rate = get_statlist(liga)
    if liga_rate:
        star_rating = round(liga_rate["win_rate"])
        stat_str = f'\n<b>Статистика лиги:</b> {star_rating}%\n' \
                   f'<b>Всего:</b> {liga_rate["all"]} Выиграно: {liga_rate["win"]}'
    else:
        stat_str = ''
    return stat_str


@logger.catch
def get_tablo(stats) -> Union[str, None]:
    """
    Функция возвращает табло статистики
    """
    str_tablo = ''
    try:
        str_tablo += f"<b>Атаки</b> {stats['Атаки'][0]} - {stats['Атаки'][1]}"
        str_tablo += f"\n<b>Опасные атаки</b> {stats['Опасные атаки'][0]} - {stats['Опасные атаки'][1]}"
        str_tablo += f"\n<b>Удары в створ</b> {stats['Удары в створ'][0]} - {stats['Удары в створ'][1]}"
        str_tablo += f"\n<b>Удары в сторону ворот</b> {stats['Удары в сторону ворот'][0]} - {stats['Удары в сторону ворот'][1]}"
        str_tablo += f"\n<b>Владение мячом %</b> {stats['Владение мячом'][0]} - {stats['Владение мячом'][1]}"
        str_tablo += f"\n<b>Угловые</b> {stats['Угловые'][0]} - {stats['Угловые'][1]}"
        if stats['Желтые карточки'][0] + stats['Желтые карточки'][1] > 0:
            str_tablo += f"\n<b>Желтые карточки</b> {stats['Желтые карточки'][0]} - {stats['Желтые карточки'][1]}"
        if stats['Красные карточки'][0] + stats['Красные карточки'][1] > 0:
            str_tablo += f"\n<b>Красные карточки</b> {stats['Красные карточки'][0]} - {stats['Красные карточки'][1]}"
    except (KeyError, TypeError):
        logger.info("Нет показателей команд")
        return None
    return str_tablo


@logger.catch
def check_game(game: Dict) -> Union[bool, None]:
    """
    Функция матч подходит ли по критерию
    """
    if check_sentlist(game['url']) or check_dumplist(game['url']):
        return False

    data_game = connect_to_match(game['id_game'])
    if not data_game:
        logger.info("Нет данных матча")
        return False
    else:
        try:
            liga_names = data_game['Value']['L']
        except (KeyError, TypeError):
            logger.info("Нет ключа имени лиги")
            return False
        if set(liga_names.split()) & OUT_LIST:  # Проверяем есть ли лига в мусорных лигах
            return False

    try:
        result_total = is_there_total(data_game['Value']['GE'])  # Проверяем есть тотал в матче
        if not result_total:
            return False
    except (KeyError, TypeError):
        logger.info("Нет тотала в матче")
        return False

    try:
        match_stats = add_stats(data_game['Value']['SC']['ST'][0]['Value'])  # Получаем статистику в матче
        if not match_stats:
            return False
    except (KeyError, TypeError):
        logger.info("Нет статистики в матче")
        return False

    if filter_events(match_stats) and CHECK_RED_CARDS:  # Проверка на красные карточки если True в конфиге
        add_dumplist(game["url"])
        return False

    if not filter_stats(match_stats):
        return False

    try:
        match_id = data_game['Value']['SGI']  # Получаем идентификатор для ссылки статистики
        if not match_stats:
            return False
        stat_url = 'https://eventsstat.com/statisticpopup/game/1/' + match_id + '/main?'
    except (KeyError, TypeError):
        logger.info("Нет идентификатора статистики")
        return False

    stat_str = get_statistic(liga_names)

    count_message = get_countlist('count')

    tablo_str = get_tablo(match_stats)

    if tablo_str is None:
        return False

    text_message = f'<i>#{count_message} Будет гол!\n' \
                   f'🏆 <b>{liga_names}</b>\n' \
                   f'<code>{game["teams"]}</code>\n' \
                   f'⚽ {game["score"]} ' \
                   f'⌚ {game["time"]}\n' \
                   f'{tablo_str}' \
                   f'\n{result_total}{stat_str}' \
                   f'\n<a href="{PARTNERS_URL}">Зарегистрироваться</a>/' \
                   f'<a href="{game["url"]}">Ставить на матч</a></i>'

    # Добавляем в список отправленных и отправляем в чат сигнал
    current_id_message = (
        bot.send_message(chat_id=ID_CHAT, text=text_message, parse_mode='html')).id

    second = int(datetime.datetime.now().timestamp())

    add_sentlist(
        id_game=game["id_game"], url=game["url"], id_message=current_id_message,
        text_message=text_message, score_sum=game['score_sum'], liga_names=liga_names, second=second,
        team_two=game["team_two"], team_one=game["team_one"], stat_url=stat_url
    )

    add_countlist('count')
