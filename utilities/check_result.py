from typing import Union, Dict

from bs4 import BeautifulSoup
from loguru import logger

from config_data.config import ID_CHAT
from datadase.sentlist_table import out_sentlist, get_sentlist, delete_sentlist
from datadase.statlist_table import add_win_statlist, add_all_statlist
from loader_telebot import bot
from utilities.other import get_request


@logger.catch()
def connect_data_match(url):
    """
    Функция возвращает json матча
    """
    params = {'ln': 'ru'}
    response_match = get_request(url, params=params)

    if response_match is not None and response_match.status_code == 200:
        page = BeautifulSoup(response_match.text, "html.parser")
        return page
    else:
        return False


@logger.catch()
def connect_result_match(data_match) -> Union[Dict, bool]:
    """
    Функция возвращает счет и исход ставки
    """
    scoreboard_info = data_match.find_all(
        "div", class_="old-scoreboard__info old-scoreboard__info--main old-scoreboard-info old-scoreboard-info--main"
    )
    if scoreboard_info:
        scoreboard_info_all = [text.strip() for text in scoreboard_info[0].text.split('\n') if text.strip() != '']
        if len(scoreboard_info_all) >= 3:
            score = scoreboard_info_all[2]
            if 'Матч состоялся' in scoreboard_info_all or 'Match finished' in scoreboard_info_all:
                score_sum = sum([int(symbol) for symbol in score if symbol.isdigit()])
            elif 'После серии пенальти' in scoreboard_info_all or 'After penalty shootout' in scoreboard_info_all:
                score_sum = sum([int(symbol) for symbol in score[1:-1] if symbol.isdigit()])
            else:
                return False
            return {'score': score, 'score_sum': score_sum}
        else:
            return False
    else:
        return False


@logger.catch()
def get_goals_time(data_match) -> str:
    """
    Функция возвращает время голов
    """

    match_chronicles = data_match.find_all("div", class_="match-chronicle__row")  # Добавляем время голов
    goals_time = ''
    if match_chronicles:
        trigger = False
        start = 1
        for row in reversed(match_chronicles):
            if start == 1 and row.text.strip() not in ('1 Тайм', '1 Half'):
                break
            start += 1

            if row.text.strip() in ('2 Тайм', '2 Half'):
                trigger = True
            elif row.text.strip() in ('ОТ', 'Overtime'):
                break
            if not trigger:
                continue
            check_row = row.find_all(
                "svg", class_='old-svg-ico old-svg-ico--soccer-ball old-svg-ico--black')
            check_row_red = row.find_all(
                "svg", class_='old-svg-ico old-svg-ico--soccer-ball old-svg-ico--red')
            if check_row or check_row_red:
                goal_time = row.find_all('div', class_='match-chronicle__time')
                if goal_time and check_row:
                    goals_time += f' ⚽{goal_time[0].text.strip()}'
                else:
                    # Добавляем вопросительный знак, так как красный мяч = незабитый пенальти или автогол
                    goals_time += f' ⚽? {goal_time[0].text.strip()}'

    return goals_time


@logger.catch()
def sleep_check_result() -> None:
    """
    Функция проверяет результат матча
    """
    logger.info("Processing the results of matches")
    out_sentlist()
    game_all = get_sentlist()
    if not game_all:
        return
    for game in game_all:
        data_match = connect_data_match(game['stat_url'])
        if not data_match:
            continue

        result_match = connect_result_match(data_match)
        if not result_match:
            continue

        text = game['text_message']
        scores = result_match['score']
        goals_time = get_goals_time(data_match)

        if result_match['score_sum'] > game['score_sum']:
            text_message = text + f'\n✅'
            add_win_statlist({'all', game['liga_names']})
        else:
            text_message = text + f'\n❌'
        stat_url = game['stat_url'].replace(
            'https://eventsstat.com/statisticpopup/game/1/', 'https://1xstavka.ru/ru/statisticpopup/game/1/'
        )

        bot.edit_message_text(
            chat_id=ID_CHAT, message_id=game['id_message'], parse_mode='html',
            text=text_message + f' <i>Счет {scores} {goals_time}\n<a href="{stat_url}">Статистика матча</a></i>')

        add_all_statlist({'all', game['liga_names']})
        delete_sentlist(game['sent_id'])
