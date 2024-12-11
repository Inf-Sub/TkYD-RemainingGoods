__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/11'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.9.0'


from os import listdir
from os.path import join as join, splitext
from asyncio import run as aio_run, get_event_loop as aio_get_event_loop
from aiomysql import connect as sql_connect, DictCursor as sql_DictCursor, Error as sql_Error
from contextlib import asynccontextmanager
from aiofiles import open as async_open
from json import loads as json_loads
from pathlib import Path
from typing import AsyncIterator, List, Dict, Any, Optional, Tuple

from config import get_db_config

from logger import logging, setup_logger

from pprint import pprint
from traceback import print_tb


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
    
    async def connect(self, loop: Optional[Any] = None) -> None:
        try:
            self.conn = await sql_connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                loop=loop,
                autocommit=False  # Устанавливаем автокоммит в False для использования транзакций
            )
            logger.info('Соединение с базой данных установлено.')
        except sql_Error as e:
            logger.error(f'Ошибка подключения к MySQL: {e}')

    async def close(self) -> None:
        if self.conn:
            self.conn.close()
            logger.info('Соединение с базой данных закрыто.')

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self.conn.cursor() as cur:
            try:
                yield cur
                await self.conn.commit()
            except Exception as e:
                await self.conn.rollback()
                logger.error(f'Ошибка транзакции: {e}')
                raise
    
    @staticmethod
    async def fetch_data(cur: Any, table: str, conditions: Optional[Dict[str, Any]] = None) -> List[Tuple[Any, ...]]:
        """
        Извлечение данных из таблицы. Условия должны быть в виде словаря, где ключи — это имена столбцов,
        а значения — искомые значения.

        :param cur: курсор для выполнения SQL-запросов
        :param table: название таблицы
        :param conditions: условия выборки данных (опционально)
        :return: список строк, соответствующих условиям
        """
        sql_query = f'SELECT * FROM {table}'

        if conditions:
            condition_clauses = ' AND '.join([f'{key} = %s' for key in conditions.keys()])
            sql_query += f' WHERE {condition_clauses}'
            await cur.execute(sql_query, tuple(conditions.values()))
        else:
            await cur.execute(sql_query)

        result = await cur.fetchall()
        return result

    async def fetch_with_dict_cursor(self, table: str, conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with self.conn.cursor(sql_DictCursor) as cur:
            return await self.fetch_data(cur, table, conditions)

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
    async def _create_table_if_not_exists(cur: Any, table: str, schema: str) -> bool:
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

    async def _load_initial_data(self, cur: Any, table: str, data_file: str) -> None:
        if data_file is None:
            return

        data_path = str(join(self.schema_dir, data_file))

        if Path(data_path).exists():
            async with async_open(data_path, 'r', encoding='utf-8') as f:
                data_content = await f.read()
                initial_data = json_loads(data_content)
                for item in initial_data:
                    await self.upsert_or_insert_data(cur, table, item)
            logger.warning(f'Данные для таблицы "{table}" загружены.')
        else:
            logger.error(f'Файл данных "{data_file}" не найден.')
    
    @staticmethod
    async def upsert_or_insert_data(cur: Any, table: str, item: Dict[str, Any], update_if_exists: bool = True) -> None:
        """
        Вставка новых данных в таблицу или, в случае конфликта, обновление существующих данных.

        :param cur: курсор для выполнения SQL-запросов
        :param table: название таблицы, в которую будут вставлены или обновлены данные
        :param item: словарь, представляющий данные для вставки или обновления, где ключи — это имена столбцов,
                     а значения — вставляемые данные
        :param update_if_exists: флаг, указывающий, следует ли обновлять данные в случае конфликта
        """
        columns = ', '.join(item.keys())
        placeholders = ', '.join(['%s'] * len(item))
        
        if update_if_exists:
            update_clause = ', '.join([f"{col} = VALUES({col})" for col in item.keys()])
            sql_query = (f'INSERT INTO {table} ({columns}) VALUES ({placeholders}) '
                         f'ON DUPLICATE KEY UPDATE {update_clause}')
        else:
            sql_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        await cur.execute(sql_query, tuple(item.values()))
        # logger.info(f'Данные для таблицы "{table}" успешно загружены{" или обновлены" if update_if_exists else ""}.')


async def update_data(wh_short_name: str, datas: List[Dict[str, Any]]) -> None:
    if not wh_short_name:
        # raise ValueError('Parameter "wh_short_name" must not be empty.')
        logger.error('Parameter "wh_short_name" must not be empty.')
        return
    
    if not datas:
        # raise ValueError('Parameter "datas" must not be empty.')
        logger.error('Parameter "datas" must not be empty.')
        return
    
    loop = aio_get_event_loop()
    db_manager = DatabaseManager()

    # Установление соединения с базой данных
    await db_manager.connect(loop)
    await db_manager.create_tables()
    
    async with db_manager.transaction() as cur:
        # Получаем ID склада 'warehouse_id' где: 'warehouse_short_name': wh_short_name
        conditions = {'warehouse_short_name': wh_short_name}
        result = await db_manager.fetch_with_dict_cursor('warehouses', conditions)
        
        if not result:
            logger.error(f'No warehouse found with short name: {wh_short_name}')
            return

        warehouse_id = result[0]['id']
        # currency_id = result[0]['currency_id']
        
        for data in datas:
            """
            Вносим данные о месте хранения или обновляем, если оно уже есть, по уникальному названию
            """
            table = 'storage_location_names'
            storage_location_names_data = {'name': data['Packing.МестоХранения']}
            await db_manager.upsert_or_insert_data(cur, table, storage_location_names_data)
            logger.info(
                f'Storage Location Name: "{storage_location_names_data["name"]}" was inserted into the "{table}" '
                f'table.')
            
            # Получаем 'location_name_id'
            if cur.lastrowid:
                location_name_id = cur.lastrowid
            else:
                conditions = {'name': data['Packing.МестоХранения']}
                result = await db_manager.fetch_with_dict_cursor(table, conditions)
                location_name_id = result[0]['id']
            
            logger.info(f'Storage Location Name ID: {location_name_id}')
            
            """
            Вносим данные о продукте или обновляем, если он уже есть, по номенклатруному номеру (barcode):
            Номенклатурный номер, артикул, размер, единицы измерения
            """
            table = 'products'
            product_data = {'barcode': data['Packing.Barcode'], 'product_name': data['Артикул'],
                'product_width': data['Packing.Ширина'], 'product_units': data['Packing.Name']}
            await db_manager.upsert_or_insert_data(cur, table, product_data)
            logger.info(
                f'Data for Product with Barcode: "{data['Packing.Barcode']}" was inserted into the "{table}" table '
                f'for Warehouse number: "{warehouse_id}" ("{wh_short_name}"). Product Name: '
                f'"{product_data["product_name"]}".')
            
            # Получаем 'product_id' после вставки продукта
            if cur.lastrowid:
                product_id = cur.lastrowid
            else:
                conditions = {'barcode': product_data['barcode']}
                result = await db_manager.fetch_with_dict_cursor(table, conditions)
                product_id = result[0]['id']
            
            logger.info(f'Product ID: {product_id}')
            
            table = 'storage_product'
            storage_product_data = {
                'product_id': product_id, 'warehouse_id': warehouse_id, 'price': data['Packing.Цена'],
                'quantity': data['Packing.Колво']}
            await db_manager.upsert_or_insert_data(cur, table, storage_product_data)
            logger.info(
                f'Data for Product ID: "{product_id}" was inserted into the "{table}" table for Warehouse number: '
                f'"{warehouse_id}" ("{wh_short_name}"). Product Price: "{storage_product_data["price"]}"; '
                f'Product Quantity: "{storage_product_data["quantity"]}".')
            
            # Получаем 'storage_product_id'
            if cur.lastrowid:
                storage_product_id = cur.lastrowid
            else:
                conditions = {
                    'product_id': storage_product_data['product_id'], warehouse_id: storage_product_data['warehouse_id']}
                result = await db_manager.fetch_with_dict_cursor(table, conditions)
                storage_product_id = result[0]['id']

            logger.info(f'Storage Product ID: {storage_product_id}')
            
            table = 'storage_locations'
            storage_locations_data = {
                'storage_product_id': storage_product_id, 'location_name_id': location_name_id}
            await db_manager.upsert_or_insert_data(cur, table, storage_locations_data)
            logger.info(
                f'Data for Storage Product ID: "{storage_product_id}" was inserted into the "{table}" table for '
                f'Warehouse "{warehouse_id}" ("{wh_short_name}"). Product Location Name: '
                f'"{storage_locations_data["location_name_id"]}".')
    
    # Закрытие соединения с базой данных
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

    shop_id = 'TOM-01'
    valid_records = [
        {'Артикул': '961/22/1/ETR', 'Packing.Barcode': '2103202475404', 'Packing.Name': 'м', 'Packing.Цена': '2640',
         'Packing.НоваяЦена': '2640', 'Packing.Скидка': '0', 'Packing.Производитель': 'NIMUE SRL',
         'Packing.СтранаПроизводства': 'Сан-Марино', 'Наименование': 'Ткань текстильная',
         'Packing.Организация': 'ООО "Дефиле"',
         'Packing.АдресПроизводителя': 'Сан-Марино, Strada Bulumina, 3 - 47899 Serravalle, Repubblica di San Marino',
         'Packing.Ширина': 140.0, 'Packing.Состав': 'ХЛОПОК 100%', 'Код': '2103202475404', 'Packing.Колво': '6',
         'Packing.Date': '27.11.2024', 'Packing.МестоХранения': 'Vip 4-2', 'Packing.СвободныйОстаток': '6'},
        {'Артикул': '607656', 'Packing.Barcode': '2100100609313', 'Packing.Name': 'шт', 'Packing.Цена': '25',
         'Packing.НоваяЦена': '25', 'Packing.Скидка': '0', 'Packing.Производитель': 'ITALIAN STOCK FASHION S.R.l.',
         'Packing.СтранаПроизводства': 'Италия', 'Наименование': 'ПУГОВИЦЫ ПЛАСТМАССОВЫЕ',
         'Packing.Организация': 'ООО "Дефиле"',
         'Packing.АдресПроизводителя': 'Via Archimede, 233/2 41019 Limidi diSoliera (МO)', 'Packing.Ширина': 23.0,
         'Packing.Состав': '', 'Код': '2100100609313', 'Packing.Колво': '34', 'Packing.Date': '27.11.2024',
         'Packing.МестоХранения': '', 'Packing.СвободныйОстаток': '34'},
        {'Артикул': '200081', 'Packing.Barcode': '2100100510046', 'Packing.Name': 'шт', 'Packing.Цена': '70',
         'Packing.НоваяЦена': '70', 'Packing.Скидка': '0', 'Packing.Производитель': 'ITALIAN STOCK FASHION S.R.l.',
         'Packing.СтранаПроизводства': 'Италия', 'Наименование': 'ЗАСТЕЖКИ-МОЛНИИ',
         'Packing.Организация': 'ООО "Дефиле"',
         'Packing.АдресПроизводителя': 'Via Archimede, 233/2 41019 Limidi diSoliera (МO)', 'Packing.Ширина': 4.3,
         'Packing.Состав': '', 'Код': '2100100510046', 'Packing.Колво': '6', 'Packing.Date': '27.11.2024',
         'Packing.МестоХранения': '', 'Packing.СвободныйОстаток': '6'}
    ]

    aio_run(update_data(shop_id, valid_records))
