import random
import time

import requests
from fake_useragent import UserAgent
from loguru import logger


@logger.catch
def get_request(url, max_retries=5, params=None):
    """
    Функция отправляет запрос на сайт
    """

    retries = 0
    while retries < max_retries:
        try:
            ua = UserAgent()
            headers = {'User-Agent': ua.chrome}
            return requests.get(url, headers=headers, params=params)
        except requests.exceptions.RequestException:
            logger.info(f"Error connecting to {url}.")
            retries += 1
            time.sleep(random.uniform(3, 5))