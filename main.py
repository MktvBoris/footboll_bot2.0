import sys
from threading import Thread

from time import sleep, localtime

from loguru import logger

from datadase.count_table import CountList, connect_with_retry
from datadase.dumplist_table import DumpList
from datadase.sentlist_table import SentList
from datadase.statlist_table import StatList, check_statistic
from utilities.check_all_games import check_all_games
from utilities.check_game import check_game
from utilities.check_result import sleep_check_result
from utilities.other import get_request


@logger.catch
def connect_to_base() -> bool:
    """
    Функция подключается к сайту, выбирает матчи и проверяет их
    """

    base_url = "https://1xstavka.ru/live/football"
    response = get_request(base_url)
    if response is None or response.status_code != 200:
        sleep(60)
        return False

    all_games = check_all_games(response)
    if all_games:
        logger.info(f'There were matches: {len(all_games)}.')
        for current_game in all_games:
            check_game(current_game)
        sleep(60)


def result_check() -> None:
    """
    Функция запускает проверку результатов матча и статистику в заданное время
    """
    while True:
        try:
            time_now = localtime()
            if time_now.tm_min in (5, 25, 45):
                sleep_check_result()
                sleep(60)
            elif time_now.tm_hour == 10 and time_now.tm_min == 00:
                check_statistic()
                sleep(60)
        except Exception as error:
            logger.info(f"Exception {error}")


@logger.catch
def create_tables() -> None:
    db = connect_with_retry()
    if db is not None:
        db.create_tables([SentList, DumpList, StatList, CountList])
        db.close()


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <yellow>{message}</yellow>", level="INFO"
    )
    logger.add(
        "runtime.log", rotation="1 days", retention="2 days",
        format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}"
    )
    logger.info("The bot is running")

    create_tables()
    Thread(target=result_check).start()

    while True:
        try:
            connect_to_base()
        except KeyboardInterrupt:
            logger.info("Completion of work")
            sys.exit()
