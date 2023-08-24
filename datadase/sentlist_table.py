from datetime import datetime
from typing import List

from loguru import logger
from peewee import AutoField, TextField, BooleanField, DateTimeField, IntegerField

from config_data.config import ID_CHAT
from datadase.count_table import BaseModel, connect_with_retry
from loader_telebot import bot


class SentList(BaseModel):
    """
    SentList
    """
    sent_id = AutoField(column_name='sent_id')
    url = TextField(column_name='url', index=True)
    id_game = IntegerField(column_name='id_game')
    stat_url = TextField(column_name='stat_url')
    issue = BooleanField(column_name='issue', index=True, default=False)
    created_date = DateTimeField(column_name='created_date')
    id_message = IntegerField(column_name='id_message')
    text_message = TextField(column_name='text_message')
    score_sum = IntegerField(column_name='score_sum')
    liga_names = TextField(column_name='liga_names')
    second = IntegerField(column_name='second')
    team_two = TextField(column_name='team_two')
    team_one = TextField(column_name='team_one')


@logger.catch
def add_sentlist(
        url: str, id_game: int, id_message: int,
        stat_url: str, text_message: str,
        score_sum: int, liga_names: str, second: int,
        team_two: str, team_one: str
) -> None:
    """
    Функция добавляет матч в таблицу SentList.
    """
    now = datetime.now()
    db = connect_with_retry()
    if db is not None:
        full_list = SentList.select().order_by(SentList.created_date)
        if full_list.count() == 50:
            full_list[0].delete_instance()

        query = SentList.select().where(SentList.url == url)
        if not query.exists():
            SentList.create(
                url=url, id_message=id_message,
                text_message=text_message, score_sum=score_sum,
                liga_names=liga_names, created_date=now,
                id_game=id_game, stat_url=stat_url, second=second,
                team_two=team_two, team_one=team_one
            )
        db.close()


@logger.catch
def delete_sentlist(sent_id: int) -> None:
    """
    Функция удаляет запись по sent_id в таблице SentList.
    """
    db = connect_with_retry()
    if db is not None:
        row = SentList.get(SentList.sent_id == sent_id)
        row.delete_instance()
        db.close()


@logger.catch
def out_sentlist():
    """
    Функция удаляет не рассчитанные ставки в таблице SentList.
    """
    db = connect_with_retry()
    if db is not None:
        full_list = SentList.select()
        for elem in full_list:
            today = datetime.now()
            created_date = elem.created_date
            time_deltadays = (today - created_date).days
            if time_deltadays > 1:
                text = elem.text_message
                message_id = elem.id_message
                text_message = text + f'\n⭕ Результаты не найдены.'

                bot.edit_message_text(
                    chat_id=ID_CHAT, message_id=message_id,
                    text=text_message, parse_mode='html')
                elem.delete_instance()
        db.close()


@logger.catch
def check_sentlist(url: str) -> bool:
    """
    Функция проверяет есть ли запись с таким url в таблице SentList.
    """
    db = connect_with_retry()
    if db is not None:
        full_list = [ex.url for ex in SentList.select()]
        db.close()
        return url in full_list


@logger.catch
def get_sentlist() -> List:
    """
    Функция возвращает записи из таблицы SentList.
    """
    db = connect_with_retry()
    if db is not None:
        full_list: List = [{'sent_id': ex.sent_id, 'url': ex.url, 'id_game': ex.id_game,
                            'stat_url': ex.stat_url, 'id_message': ex.id_message, 'liga_names': ex.liga_names,
                            'text_message': ex.text_message, 'score_sum': ex.score_sum,
                            'second': ex.second, 'team_one': ex.team_one, 'team_two': ex.team_two,
                            } for ex in SentList.select()]
        db.close()
        return full_list
