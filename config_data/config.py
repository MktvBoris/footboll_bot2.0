import os

from dotenv import find_dotenv, load_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл ..env')
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ID_CHAT = os.getenv('ID_CHAT')
PARTNERS_URL = os.getenv('PARTNERS_URL')
SCORE_DIFFERENCE = int(os.getenv('SCORE_DIFFERENCE'))
SCORE_ONE_TIME = int(os.getenv('SCORE_ONE_TIME'))
CHECK_CUR_SCORES = True  # Нужно ли чтобы счет с начала 2 тайма не изменился
TIME_SORT_START = int(os.getenv('TIME_SORT_START'))
TIME_SORT_END = int(os.getenv('TIME_SORT_END'))
ATTACKS = int(os.getenv('ATTACKS'))
DANGEROUS_ATTACKS = int(os.getenv('DANGEROUS_ATTACKS'))
SHOTS_ON_TARGET = int(os.getenv('SHOTS_ON_TARGET'))
SHOTS_TOWARDS_THE_GOAL = int(os.getenv('SHOTS_TOWARDS_THE_GOAL'))
CORNERS = int(os.getenv('CORNERS'))
CHECK_RED_CARDS = True  # Нужно ли проверять наличие красных карточек в матче

OUT_LIST = {
    '5x5', 'League', '5x5', '6x6', 'ACL', '4x4', '2x2', '3x3', '3x3.', 'Short', 'Ligue', 'Женщины',
    'Товарищеский', 'Кубок', 'УЕФА', 'лет', 'года', 'Сборные', 'Товарищеские', 'кубок'
}


