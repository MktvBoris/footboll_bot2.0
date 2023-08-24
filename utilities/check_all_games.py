import re
from time import sleep
from typing import List, Union, Dict

from bs4 import BeautifulSoup
from loguru import logger

from config_data.config import TIME_SORT_START, TIME_SORT_END, SCORE_DIFFERENCE, SCORE_ONE_TIME, \
    CHECK_CUR_SCORES
from datadase.dumplist_table import check_dumplist, add_dumplist
from datadase.sentlist_table import check_sentlist


@logger.catch
def check_scores(scores) -> Union[bool, Dict]:
    """
    Функция проверяет на критерии отбора счета и возвращает счет обеих команд и его сумму
    """

    scores = [int(score.text.strip()) for score in scores]
    score_1t, score_1t_1t = scores[0], scores[1]
    if len(scores) == 4:
        score_2t, score_2t_1t = scores[2], scores[3]
    else:
        score_2t, score_2t_1t = scores[3], scores[4]

    scores_cur, scores_1t = score_1t + score_2t, score_1t_1t + score_2t_1t
    score_dif = abs(score_1t - score_2t)
    if 0 == score_dif or score_dif > SCORE_DIFFERENCE:  # Если разница мячей равно 0 или больше чем SCORE_DIFFERENCE
        return False

    elif (score_1t_1t + score_2t_1t) < SCORE_ONE_TIME:  # Если голы в первом тайме меньше SCORE_ONE_TIME
        return False

    elif CHECK_CUR_SCORES and scores_cur != scores_1t:  # Если счет после первого тайма изменился
        return False

    return {'score_one_team': score_1t, 'score_two_team': score_2t, 'score_sum': score_1t + score_2t}


@logger.catch
def check_time(time, url) -> Union[bool, str]:

    """
    Функция проверяет и возвращает время матча
    """
    time = time[0].text.strip()
    time_correct = tuple(range(TIME_SORT_START, TIME_SORT_END + 1))
    pattern = r"1-й Тайм|Перерыв"

    if time[0:2].isdigit():
        time_check: int = int(time[0:2])
    else:
        return False
    if re.search(pattern, time):
        return False
    if time_check not in time_correct:
        if time_check > TIME_SORT_END:
            add_dumplist(url)
            return False
        return False
    return time.replace('\n', ' ')


@logger.catch
def get_url_and_id(url) -> Dict:
    """
    Функция url и айди лиги и матча
    """
    str_clean = url[0].get('href').split('/')
    id_game = int(str_clean[3].split('-')[0])

    # Получаем ссылку на матч
    url = 'https://1xstavka.ru/' + url[0].get('href')
    return {'url': url, 'id_game': id_game}


@logger.catch
def check_all_games(results):
    """
    Функция выбирает из матчей в лайф подходящие по критерию
    """

    page = BeautifulSoup(results.text, "html.parser")
    clean_result: List = []
    # Получаем матчи
    games = page.find_all("div", class_="c-events__item c-events__item_col")
    if not games:
        logger.info("Нет матчей")
        return
    for game in games:
        sleep(1)
        url = game.find_all("a")
        if not url:
            logger.info("Нет url")
            continue
        url_clean = get_url_and_id(url=url)
        if check_sentlist(url_clean['url']) or check_dumplist(url_clean['url']):
            continue

        # Получаем время матча
        time = game.find_all("div", class_="c-events__time")
        if not time:
            logger.info(f"Нет времени в матче {url_clean['url']}")
            continue
        time_clean = check_time(time=time, url=url_clean['url'])
        if not time_clean:
            continue

        # Получаем счет матча и проверяем по нужному критерию
        scores = game.find_all("span", class_="c-events-scoreboard__cell")
        if not scores or len(scores) not in (4, 6):
            continue
        scores_clean = check_scores(scores)
        if not scores_clean:
            continue

        # Получаем названия команд
        team_names = game.find_all("span", class_="c-events__team")
        if not team_names:
            logger.info("Нет названия команд")
            continue
        team_one, team_two = team_names[0].text.strip(), team_names[1].text.strip()

        # Добавляем в словарь нужные значения
        current_game = {
            'teams': f'{team_one} - {team_two}', 'time': time_clean, 'score_sum': scores_clean['score_sum'],
            'id_game': url_clean['id_game'], 'url': url_clean['url'],
            'score': f"{scores_clean['score_one_team']} - {scores_clean['score_two_team']}",
            'team_one': team_one, 'team_two': team_two
        }
        clean_result.append(current_game)

    return clean_result
