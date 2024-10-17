__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/06'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.5.1'


from os import listdir
from os.path import join, splitext
import asyncio
import aiomysql
from aiofiles import open as async_open
from json import loads as json_loads
from pathlib import Path

from app.utils.logging_config import logging, setup_logging


setup_logging()
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, host, port, database, user, password, schema_dir, schema_json):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.schema_dir = schema_dir
        self.schema_json = schema_json

    async def connect(self, loop):
        try:
            self.conn = await aiomysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                loop=loop
            )
            logger.info('Соединение с базой данных установлено.')
        except aiomysql.Error as e:
            logger.error(f'Ошибка подключения к MySQL: {e}')

    async def close(self):
        if self.conn:
            self.conn.close()
            logger.info('Соединение с базой данных закрыто.')

    async def create_tables(self) -> None:
        async with self.conn.cursor() as cur:
            schema_json_path = str(join(self.schema_dir, self.schema_json))

            if Path(schema_json_path).exists():
                # Загрузка порядка файлов из JSON
                async with async_open(schema_json_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    schema_files_info = json_loads(content)
            else:
                # Загрузка файлов из директории (алфавитный порядок)
                schema_files_info = {
                    'order': [
                        filename for filename in listdir(self.schema_dir)
                        if filename.startswith('schema') and filename.endswith('.sql')
                    ],
                    'data': {}
                }

            tables = await self._load_schemas(schema_files_info['order'])
            for table, schema in tables.items():
                if await self._create_table_if_not_exists(cur, table, schema):
                    # If table is created, insert the initial data if available
                    # Инициализация данных, если они указаны в файле конфигурации
                    if table in schema_files_info.get('data', {}):
                        await self._load_initial_data(cur, table, schema_files_info['data'][table])

        await self.conn.commit()  # Commit all changes once tables are created and data is loaded

    async def _load_schemas(self, order: list) -> dict:
        tables = {}
        for filename in order:
            table_name = splitext(filename)[0].replace('schema_', '')

            async with async_open(join(self.schema_dir, filename), 'r', encoding='utf-8') as f:
                content = await f.read()
                tables[table_name] = content
        return tables

    @staticmethod
    async def _create_table_if_not_exists(cur, table, schema) -> bool:
        await cur.execute(f"SHOW TABLES LIKE '{table}';")
        result = await cur.fetchone()

        if result:
            logger.info(f"Таблица '{table}' существует.")
            return False
        else:
            logger.info(f"Таблица '{table}' не найдена. Создание таблицы...")
            await cur.execute(schema)
            logger.info(f"Таблица '{table}' успешно создана.")
            return True

    async def _load_initial_data(self, cur, table, data_file) -> None:
        data_path = str(join(self.schema_dir, data_file))

        if Path(data_path).exists():
            async with async_open(data_path, 'r', encoding='utf-8') as f:
                data_content = await f.read()
                data = json_loads(data_content)
                for item in data:
                    await self._insert_data(cur, table, item)
            logger.info(f"Данные для таблицы '{table}' загружены.")
        else:
            logger.error(f"Файл данных '{data_file}' не найден.")

    @staticmethod
    async def _insert_data(cur, table, item) -> None:
        # Пример вставки данных, ожидается, что item - это словарь
        columns = ', '.join(item.keys())
        placeholders = ', '.join(["%s"] * len(item))
        sql_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        await cur.execute(sql_query, tuple(item.values()))
        # logger.info(f"Данные для таблицы '{table}' загружены.")

    # Пример структуры schema_order.json:
    # {
    #     "order": [
    #         "schema_cities.sql",
    #         "schema_stores.sql"
    #     ],
    #     "data": {
    #         "cities": "datas_cities.json",
    #         "stores": "datas_stores.json"
    #     }
    # }


async def main():
    loop = asyncio.get_event_loop()
    db_manager = DatabaseManager(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD,
        schema_dir=DATA_DIR, schema_json=DB_INIT_SCHEMAS)

    await db_manager.connect(loop)
    # db_manager = DatabaseManager(conn, schema_dir)
    await db_manager.create_tables()

    await db_manager.close()


if __name__ == '__main__':
    # from os.path import join
    from os import getenv
    from dotenv import load_dotenv

    from app.config import DATA_DIR

    # Загрузка переменных из .env файла
    load_dotenv()

    DB_HOST = getenv('DB_HOST')
    DB_PORT = int(getenv('DB_PORT'))
    DB_NAME = getenv('DB_NAME')
    DB_USERNAME = getenv('DB_USERNAME')
    DB_PASSWORD = getenv('DB_PASSWORD')

    # DB_INIT_DATA_CITIES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_CITIES_FILE_PATH'))
    # DB_INIT_DATA_STORES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_STORES_FILE_PATH'))
    DB_INIT_SCHEMAS = getenv('DB_INIT_SCHEMAS')

    asyncio.run(main())
