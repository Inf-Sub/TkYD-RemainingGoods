__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/28'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.7.0'


from os import listdir
from os.path import join as join, splitext
from asyncio import run as aio_run, get_event_loop as aio_get_event_loop
from pprint import pprint
from traceback import print_tb

from aiomysql import connect as sql_connect, Error as sql_Error
from aiofiles import open as async_open
from json import loads as json_loads
from pathlib import Path

from colorlog import exception

from config import get_db_config

from logger import logging, setup_logger


setup_logger()
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.env = get_db_config()

        self.host = self.env['host']
        self.port = self.env['port']
        self.user = self.env['user']
        self.password = self.env['password']
        self.database = self.env['database']
        self.schema_dir = self.env['db_schema_dir']
        self.schema_json = self.env['db_file_init_schema']
        self.table_prefix = self.env['db_file_table_prefix']
        self.init_data_prefix = self.env['db_file_init_data_prefix']
        self.conn = None

    async def connect(self, loop):
        try:
            self.conn = await sql_connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                loop=loop
            )
            logger.info('Соединение с базой данных установлено.')
        except sql_Error as e:
            logger.error(f'Ошибка подключения к MySQL: {e}')

    async def close(self):
        if self.conn:
            self.conn.close()
            logger.info('Соединение с базой данных закрыто.')

    async def create_tables(self) -> None:
        async with self.conn.cursor() as cur:
            schema_json_path = str(join(self.schema_dir, self.schema_json))

            if Path(schema_json_path).exists():
                logger.info(
                    f'Файл схемы: {schema_json_path} - найден, загружаем списки таблиц и фвйлов данных для '
                    f'инициализации в порядке, указанном в файле.')
                # Загрузка порядка файлов из файла схемы в формате JSON
                async with async_open(schema_json_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    schema_files_info = json_loads(content)
            else:
                logger.warning(
                    f'Файл схемы: {schema_json_path} - не найден, загружаем списки таблиц и фвйлов данных для '
                    f'инициализации в алфавитном порядке.')
                # Загрузка файлов из директории (алфавитный порядок)
                schema_files_info = {
                    self.table_prefix: [
                        filename for filename in listdir(self.schema_dir)
                        if filename.startswith(self.table_prefix) and filename.endswith('.sql')
                    ],
                    self.init_data_prefix: {}
                }

            if self.table_prefix in schema_files_info:
            # if schema_files_info.get(self.table_prefix, {}):
                logger.info(f'Список файлов таблиц БД загружен.')

                tables = await self._load_schemas(schema_files_info[self.table_prefix])

                for table, schema in tables.items():
                    if await self._create_table_if_not_exists(cur, table, schema):
                        # Инициализация данных, из файла с шаблонным названием: "initial_data_{table}.json" (при наличии)
                        data_file = f'{self.init_data_prefix}_{table}.json'

                        # If table is created, insert the initial data if available
                        # Инициализация данных, если имя файла указано в файле схемы
                        if table in schema_files_info.get(self.init_data_prefix, {}):
                            logger.info(f'Имя таблицы: "{table}" найдено в списке импорта инициализационных данных.')
                            data_file = schema_files_info[self.init_data_prefix][table]

                        logger.info(f'Файл инициализации данных: "{data_file}".')

                        await self._load_initial_data(cur, table, data_file)

            else:
                logger.error(f'Список файлов таблиц БД пуст или префикс "{self.table_prefix}" указан не верно.')

        await self.conn.commit()  # Commit all changes once tables are created and initial data is loaded

    async def _load_schemas(self, files_list: list) -> dict:
        tables = {}
        for filename in files_list:
            table_name = splitext(filename)[0].replace(f'{self.table_prefix}_', '')

            async with async_open(join(self.schema_dir, filename), 'r', encoding='utf-8') as f:
                content = await f.read()
                tables[table_name] = content
        return tables

    @staticmethod
    async def _create_table_if_not_exists(cur, table, schema) -> bool:
        await cur.execute(f'SHOW TABLES LIKE "{table}";')
        result = await cur.fetchone()

        if result:
            logger.info(f'Таблица "{table}" существует.')
            return False
        else:
            logger.warning(f'Таблица "{table}" не найдена. Создание таблицы...')
            await cur.execute(schema)
            logger.warning(f'Таблица "{table}" успешно создана.')
            return True

    async def _load_initial_data(self, cur, table, data_file) -> None:
        if data_file is None:
            return

        data_path = str(join(self.schema_dir, data_file))

        if Path(data_path).exists():
            async with async_open(data_path, 'r', encoding='utf-8') as f:
                data_content = await f.read()
                initial_data = json_loads(data_content)
                for item in initial_data:
                    await self._insert_data(cur, table, item)
            logger.warning(f'Данные для таблицы "{table}" загружены.')
        else:
            logger.error(f'Файл данных "{data_file}" не найден.')

    @staticmethod
    async def _insert_data(cur, table, item) -> None:
        # Вставка данных, ожидается, что item - это словарь
        columns = ', '.join(item.keys())
        placeholders = ', '.join(['%s'] * len(item))
        sql_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        await cur.execute(sql_query, tuple(item.values()))
        # logger.info(f'Данные для таблицы "{table}" загружены.')

    # Пример структуры schema_db.json:
    # {
    #     "files_list": [
    #         "schema_cities.sql",
    #         "schema_stores.sql"
    #     ],
    #     "data": {
    #         "cities": "data_cities.json",
    #         "stores": "data_stores.json"
    #     }
    # }


async def main():
    loop = aio_get_event_loop()
    db_manager = DatabaseManager()

    await db_manager.connect(loop)
    await db_manager.create_tables()
    await db_manager.close()
    # try:
    #     await db_manager.connect(loop)
    #     await db_manager.create_tables()
    # except Exception as e:
    #     logger.error(f'Ошибка в процессе выполнения: {e}')
    # finally:
    #     await db_manager.close()


if __name__ == '__main__':
    # from asyncio import get_running_loop as aio_get_loop
    # from os.path import join as join
    # from os import getenv
    # from dotenv import load_dotenv

    # from config import DATA_DIR

    # Загрузка переменных из .env файла
    # load_dotenv()

    # DB_HOST = getenv('DB_HOST')
    # DB_PORT = int(getenv('DB_PORT'))
    # DB_NAME = getenv('DB_NAME')
    # DB_USERNAME = getenv('DB_USERNAME')
    # DB_PASSWORD = getenv('DB_PASSWORD')

    # DB_INIT_DATA_CITIES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_CITIES_FILE_PATH'))
    # DB_INIT_DATA_STORES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_STORES_FILE_PATH'))
    # DB_INIT_SCHEMAS = getenv('DB_INIT_SCHEMAS')

    aio_run(main())
