import time
from datetime import datetime

from loguru import logger
from peewee import AutoField, TextField, IntegerField, Model, SqliteDatabase, OperationalError

now = datetime.now


@logger.catch
def connect_with_retry(max_retries=5, retry_delay=3):
    retries = 0
    while retries < max_retries:
        try:
            db = BaseModel._meta.database
            db.connect()
            return db
        except OperationalError:
            retries += 1
            time.sleep(retry_delay)
    logger.info("Превышено количество попыток подключения")
    return None


class BaseModel(Model):
    """
    Базовая модель
    """

    class Meta:
        database = SqliteDatabase('db_75.sqlite')


class CountList(BaseModel):
    """
    CountList
    """
    stat_id = AutoField(column_name='sent_id')
    name = TextField(column_name='name_stat', index=True)
    number_sent = IntegerField(column_name='number_sent', default=0)


@logger.catch
def add_countlist(name: str) -> None:
    """
    Функция прибавляет счетчик в таблицу CountList.
    """
    db = connect_with_retry()
    if db is not None:
        query = CountList.select().where(CountList.name == name)

        if not query.exists():
            CountList.create(name=name, number_sent=1)
        else:
            row = CountList.get(CountList.name == name)
            row.number_sent = row.number_sent + 1
            row.save()
        db.close()


@logger.catch
def get_countlist(name: str) -> int:
    """
    Функция возвращает записи в таблице StatList.
    """
    db = connect_with_retry()
    if db is not None:
        query = CountList.select().where(CountList.name == name)
        if not query.exists():
            CountList.create(name=name, number_sent=1)
            db.close()
            return 1
        else:
            row = CountList.get(CountList.name == name)
            db.close()
            return row.number_sent
