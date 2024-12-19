__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.9.9'


from os import listdir
from os.path import join as join, splitext
from asyncio import run as aio_run, get_event_loop as aio_get_event_loop
from aiomysql import connect as sql_connect, DictCursor as sql_DictCursor, Error as sql_Error
from contextlib import asynccontextmanager
from aiofiles import open as async_open
from json import loads as json_loads
from pathlib import Path
from typing import AsyncIterator, List, Dict, Any, Optional, Tuple

from csv_keys import get_csv_keys
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
    
    async def connect(self, loop: Optional[Any] = None, db: Optional[str] = None) -> bool:
        """
        Устанавливает асинхронное соединение с MySQL базой данных с использованием указанных конфигурационных
        параметров.
    
        :param loop: Опционально. Событийный цикл, который будет использоваться для асинхронного подключения.
        Если не указан, используется текущий событийный цикл.
        :param db: Опционально. Название базы данных, к которой следует подключиться.
        Если не указано, используется значение из конфигурации self.database.
    
        :return: Возвращает True, если соединение было успешно установлено, и False в случае ошибки.
        
        В случае успешного подключения устанавливает атрибут self.conn, который хранит объект соединения.
        При возникновении ошибки логирует сообщение об ошибке и возвращает False.
        """
        try:
            self.conn = await sql_connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=db if db is not None else self.database,
                loop=loop,
                autocommit=False
            )
            logger.info('Соединение с базой данных установлено.')
            return True
        except sql_Error as e:
            logger.error(f'Ошибка подключения к MySQL: {e}')
            return False

    async def close(self) -> None:
        """
        Закрывает соединение с базой данных, если оно активно.

        После выполнения этого метода объект соединения становится недоступным
        для других операций до повторного вызова метода connect().
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info('Соединение с базой данных закрыто.')

    @asynccontextmanager
    async def transaction(self, data: Dict[str, Any]) -> AsyncIterator[None]:
        """
        Контекстный менеджер для выполнения транзакций.

        Использует курсор для выполнения операций с базой данных.
        В случае успешного выполнения транзакция подтверждается (commit),
        при возникновении исключения транзакция отменяется (rollback).

        :param data: Данные, связанные с транзакцией, используемые для логирования в случае исключения.
        """
        async with self.conn.cursor() as cur:
            try:
                yield cur
                await self.conn.commit()
            except Exception as e:
                await self.conn.rollback()
                logger.error(f'Transaction error: {e}. Data: {data}')
                raise

    async def create_database(self) -> None:
        """
        Асинхронно создает базу данных, если она не существует.

        Метод устанавливает временное подключение к 'information_schema', чтобы проверить, существует ли база данных
        с именем, указанным в self.database. Если база данных не найдена, она будет создана.

        В случае ошибки подключения или выполнения SQL-запроса, ошибка логируется и выбрасывается исключение для
        последующей обработки.

        Исключения:
            OperationalError: Если происходит ошибка при подключении или выполнение SQL-запроса.
        """
        try:
            if await self.connect(db='information_schema'):
                async with self.conn.cursor() as cur:
                    # Проверяем, существует ли база данных
                    await cur.execute(
                        'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s', (self.database,))
                    result = await cur.fetchone()
                    if not result:
                        # Если база данных не существует, создаем ее
                        await cur.execute(f'CREATE DATABASE `{self.database}`')
                        logger.warning(f'База данных {self.database} успешно создана.')
                    else:
                        logger.info(f'База данных {self.database} уже существует.')
        except sql_Error as e:
            logger.error(f'Ошибка при создании базы данных: {e}')
            raise
        finally:
            await self.close()  # Закрываем временное соединение

    async def create_tables(self) -> None:
        """
        Создаёт структуры таблиц в базе данных на основе схем, определенных в файлах.

        Загружает схемы таблиц из JSON-файла, если он существует, или в алфавитном порядке из указанной директории.
        Попытка создать каждую таблицу, если она не существует, и инициализировать данные, используя соответствующие файлы.

        :return: None
        """
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

    async def fetch_with_dict_cursor(
            self, table: str, conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Извлекает данные из таблицы, используя курсор, возвращающий строки в виде словарей.

        :param table: Название таблицы, из которой необходимо извлечь данные.
        :param conditions: Словарь условий для выборки данных (опционально).
        :return: Список словарей, где каждый словарь представляет строку данных с именами столбцов в качестве ключей.
        """
        async with self.conn.cursor(sql_DictCursor) as cur:
            return await self.fetch_data(cur, table, conditions)

    async def _load_schemas(self, files_list: list) -> dict:
        """
        Асинхронно загружает схемы таблиц из списка файлов.

        :param files_list: Список файлов, содержащих схемы таблиц.
        :return: Словарь, где ключами являются имена таблиц, а значениями — содержимое файлов схем.
        """
        tables = {}
        for filename in files_list:
            table_name = splitext(filename)[0].replace(f'{self.table_prefix}_', '')

            async with async_open(join(self.schema_dir, filename), 'r', encoding='utf-8') as f:
                content = await f.read()
                tables[table_name] = content
        return tables

    @staticmethod
    async def _create_table_if_not_exists(cur: Any, table: str, schema: str) -> bool:
        """
        Асинхронно проверяет существование таблицы в базе данных и создает её, если она не существует.

        :param cur: Курсор базы данных для выполнения SQL-запросов.
        :param table: Имя таблицы.
        :param schema: SQL-схема для создания таблицы.
        :return: Булево значение, указывающее на то, была ли таблица создана (True) или уже существовала (False).
        """
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
        """
        Асинхронно загружает начальные данные в указанную таблицу из файла.

        :param cur: Курсор базы данных для выполнения SQL-запросов.
        :param table: Имя таблицы для загрузки данных.
        :param data_file: Имя файла, содержащего начальные данные в формате JSON.
        """
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
            update_clause = ', '.join([f'{col} = VALUES({col})' for col in item.keys()])
            sql_query = (f'INSERT INTO {table} ({columns}) VALUES ({placeholders}) '
                         f'ON DUPLICATE KEY UPDATE {update_clause}')
        else:
            sql_query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        try:
            await cur.execute(sql_query, tuple(item.values()))
        except Exception as e:
            logger.error(f'Ошибка выполнения SQL-запроса: {e}. SQL-query: {sql_query}. Values: {tuple(item.values())}')
    
    # logger.info(f'Данные для таблицы "{table}" успешно загружены{" или обновлены" if update_if_exists else ""}.')
    

# async def get_materials(fetch) -> Dict[str, int]:
#     materials_result = await fetch('materials')
#
#     if not materials_result:
#         logger.error(f'No materials found.')
#         return
#
#     return {material['material_name']: compound['id'] for compound in compounds_result}


async def get_compound(fetch_function: Any) -> Optional[Dict[str, int]]:
    try:
        compounds_result = await fetch_function('materials')
        if not compounds_result:
            logger.error('No materials found.')
            return None

        return {compound['material_name']: compound['id'] for compound in compounds_result}
    except Exception as e:
        logger.exception(f"Failed to fetch materials: {e}")
        return None
    

async def update_data(wh_short_name: str, datas: List[Dict[str, Any]]) -> None:
    log_warn_view = False
    
    if not wh_short_name:
        logger.error('Parameter "wh_short_name" must not be empty.')
        return

    if not datas:
        logger.error('Parameter "datas" must not be empty.')
        return

    keys = get_csv_keys()
    loop = aio_get_event_loop()
    db_manager = DatabaseManager()

    # Создаем базу данных, если ее нет
    await db_manager.create_database()

    # Установление соединения с базой данных
    if not await db_manager.connect(loop):
        logger.error('Exit: Ошибка подключения к базе данных.')
        return
    
    await db_manager.create_tables()
    
    # Получаем ID склада
    warehouse_conditions = {'warehouse_short_name': wh_short_name}
    warehouse_result = await db_manager.fetch_with_dict_cursor('warehouses', warehouse_conditions)
    
    if not warehouse_result:
        logger.error(f'No warehouse found with short name: {wh_short_name}')
        return
    
    warehouse_id = warehouse_result[0]['id']
    
    # Получаем список материалов
    materials_dict = await get_compound(db_manager.fetch_with_dict_cursor)
    if not materials_dict:
        logger.error(f'Dictionary with Materials not found in DB.')
        return
    

    # version 2
    for data in datas:
        try:
            async with db_manager.transaction(data) as cur:
                # logger.info(f'Created transaction for Shop: {wh_short_name}, Barcode: {data["Packing.Barcode"]}')

                # keys['barcode'] = 'Packing.Barcode'
                # keys['article'] = 'Артикул'
                # keys['width'] = 'Packing.Ширина'
                # keys['unit_name'] = 'Packing.Name'
                # keys['storage_location'] = 'Packing.МестоХранения'
                # keys['compound'] = 'Packing.Состав'
                # keys['quantity'] = 'Packing.Колво'
                # keys['price'] = 'Packing.Цена'
                
                location_name_ids = []  # Список идентификаторов мест хранения
                if keys['storage_location'] in data and data[keys['storage_location']]:
                    # print(f'Shop: {wh_short_name}, {keys['storage_location']}, {data[keys['storage_location']]}')
                    table = 'storage_location_names'
                    for location_name in data[keys['storage_location']]:
                        # print(f'Shop: {wh_short_name}, {keys['storage_location']}, {location_name}')
                        conditions = {'name': location_name}
                        await db_manager.upsert_or_insert_data(cur, table, conditions)
                        
                        location_name_id = cur.lastrowid or (
                            await db_manager.fetch_with_dict_cursor(table, conditions))[0]['id']
                        # print(f'Shop: {wh_short_name}, location_name_id: {location_name_id}')
                        location_name_ids.append(location_name_id)
                        # print(f'Shop: {wh_short_name}, location_name_ids: {location_name_ids}')
                else:
                    if log_warn_view:
                        logger.warning(
                            f'Shop: {wh_short_name}. Storage Location Names are empty: {data[keys['barcode']]}')
                
                table = 'products'
                conditions = {'barcode': data[keys['barcode']], 'product_name': data[keys['article']],
                    'product_units': data[keys['unit_name']]}

                # Добавляем условие для ширины только если значение не None или тип количества не равен метрам
                if data[keys['width']] is not None or (data[keys['unit_name']] is not None and data[keys['unit_name']].lower() != 'м'):
                    conditions['product_width'] = data[keys['width']]
                    # print(f'Shop: {wh_short_name}, added "{keys['width']}" to {conditions}')
                
                await db_manager.upsert_or_insert_data(cur, table, conditions)
                
                product_id = cur.lastrowid or (
                    await db_manager.fetch_with_dict_cursor(table, {'barcode': conditions['barcode']}))[0]['id']
                
                table = 'storage_product'
                conditions = {'product_id': product_id, 'warehouse_id': warehouse_id, 'price': data[keys['price']],
                    'quantity': data[keys['quantity']]}
                
                await db_manager.upsert_or_insert_data(cur, table, conditions)
                
                if location_name_ids:
                    storage_product_id = cur.lastrowid or (await db_manager.fetch_with_dict_cursor(table, {
                        'product_id': product_id, 'warehouse_id': warehouse_id}))[0]['id']
                    
                    table = 'storage_locations'
                    for location_name_id in location_name_ids:
                        conditions = {'storage_product_id': storage_product_id, 'location_name_id': location_name_id}
                        await db_manager.upsert_or_insert_data(cur, table, conditions)

                # Обработка и импорт данных о составе
                if keys['compound'] in data and data[keys['compound']]:
                    # print(f'Shop: {wh_short_name}, keys['compound']: {keys['compound']}, {data[keys['compound']]}')
                    for compound_name, proportion in data[keys['compound']].items():
                        # print(f'Shop: {wh_short_name}, keys['compound']: {keys['compound']}, compound_name: {compound_name},'
                        #       f' {proportion}')
                        if compound_name in materials_dict:
                            material_id = materials_dict[compound_name]
                            # print(f'Shop: {wh_short_name}, compound_name: {compound_name}, material_id: {material_id}')
                            table = 'product_materials'
                            conditions = {
                                'product_id': product_id, 'material_id': material_id, 'proportion': proportion}
                            await db_manager.upsert_or_insert_data(cur, table, conditions)
                        else:
                            if log_warn_view:
                                logger.warning(
                                    f'Shop: {wh_short_name}. Compound name: "{compound_name}" is not found in DB.')
                
                # logger.info(f'Finished transaction for Shop: {wh_short_name}, Barcode: {data[keys['barcode']]}')
        except Exception as e:
            logger.error(
                f'Failed to update data for Shop: {wh_short_name}, Barcode: {data[keys['barcode']]}. Error: {e}. '
                f'Data: {data}')
    
    await db_manager.close()
    
    # version 1
    # for data in datas:
    #     try:
    #         async with db_manager.transaction(data) as cur:
    #             # logger.info(f'Created transaction for Shop: {wh_short_name}, Barcode: {data["Packing.Barcode"]}')
    #
    #             keys['storage_location'] = 'Packing.МестоХранения'
    #             if keys['storage_location'] in data and data[keys['storage_location']]:
    #                 table = 'storage_location_names'
    #                 conditions = {'name': data[keys['storage_location']]}
    #                 await db_manager.upsert_or_insert_data(cur, table, conditions)
    #
    #                 location_name_id = cur.lastrowid or (
    #                     await db_manager.fetch_with_dict_cursor(table, conditions))[0]['id']
    #             else:
    #                 logger.warning(f'Storage Location Name is empty: {data["Packing.Barcode"]}')
    #                 location_name_id = None
    #
    #             table = 'products'
    #             conditions = {'barcode': data['Packing.Barcode'], 'product_name': data['Артикул'],
    #                           'product_width': data['Packing.Ширина'], 'product_units': data['Packing.Name']}
    #             await db_manager.upsert_or_insert_data(cur, table, conditions)
    #
    #             product_id = cur.lastrowid or (
    #                 await db_manager.fetch_with_dict_cursor(table, {'barcode': conditions['barcode']})
    #             )[0]['id']
    #
    #             table = 'storage_product'
    #             conditions = {'product_id': product_id, 'warehouse_id': warehouse_id, 'price': data['Packing.Цена'],
    #                           'quantity': data['Packing.Колво']}
    #             await db_manager.upsert_or_insert_data(cur, table, conditions)
    #
    #             if keys['storage_location'] in data and data[keys['storage_location']]:
    #                 storage_product_id = cur.lastrowid or (await db_manager.fetch_with_dict_cursor(table, {
    #                     'product_id': product_id, 'warehouse_id': warehouse_id}))[0]['id']
    #
    #                 table = 'storage_locations'
    #                 conditions = {'storage_product_id': storage_product_id, 'location_name_id': location_name_id}
    #                 await db_manager.upsert_or_insert_data(cur, table, conditions)
    #
    #
    #             # logger.info(f'Finished transaction for Shop: {wh_short_name}, Barcode: {data["Packing.Barcode"]}')
    #     except Exception as e:
    #         logger.error(
    #             f'Failed to update data for Shop: {wh_short_name}, Barcode: {data["Packing.Barcode"]}. Error: {e}.')
    #
    # await db_manager.close()


# async def update_data(wh_short_name: str, datas: List[Dict[str, Any]]) -> None:
#     if not wh_short_name:
#         # raise ValueError('Parameter "wh_short_name" must not be empty.')
#         logger.error('Parameter "wh_short_name" must not be empty.')
#         return
#
#     if not datas:
#         # raise ValueError('Parameter "datas" must not be empty.')
#         logger.error('Parameter "datas" must not be empty.')
#         return
#
#     loop = aio_get_event_loop()
#     db_manager = DatabaseManager()
#
#     # Установление соединения с базой данных
#     await db_manager.connect(loop)
#     await db_manager.create_tables()
#
#     async with db_manager.transaction() as cur:
#         # Получаем ID склада 'warehouse_id' где: 'warehouse_short_name': wh_short_name
#         conditions = {'warehouse_short_name': wh_short_name}
#         result = await db_manager.fetch_with_dict_cursor('warehouses', conditions)
#
#         if not result:
#             logger.error(f'No warehouse found with short name: {wh_short_name}')
#             return
#
#         warehouse_id = result[0]['id']
#         # currency_id = result[0]['currency_id']
#
#         for data in datas:
#             print(wh_short_name, data)
#             """
#             Вносим данные о месте хранения или обновляем, если оно уже есть, по уникальному названию
#             """
#             keys['storage_location'] = 'Packing.МестоХранения'
#             if keys['storage_location'] in data and data[keys['storage_location']]:
#                 table = 'storage_location_names'
#                 conditions = {'name': data[keys['storage_location']]}
#                 await db_manager.upsert_or_insert_data(cur, table, conditions)
#                 logger.info(
#                     f'Storage Location Name: "{conditions["name"]}" was inserted into the "{table}" '
#                     f'table.')
#
#                 # Получаем 'location_name_id'
#                 if cur.lastrowid:
#                     location_name_id = cur.lastrowid
#                 else:
#                     conditions = {'name': data[keys['storage_location']]}
#                     result = await db_manager.fetch_with_dict_cursor(table, conditions)
#                     location_name_id = result[0]['id']
#
#                 logger.info(f'Storage Location Name ID: {location_name_id} for Name: {data[keys['storage_location']]}')
#             else:
#                 logger.warning(f'Storage Location Name is empty: {data["Packing.Barcode"]}')
#
#             """
#             Вносим данные о продукте или обновляем, если он уже есть, по номенклатруному номеру (barcode):
#             Номенклатурный номер, артикул, размер, единицы измерения
#             """
#             table = 'products'
#             conditions = {'barcode': data['Packing.Barcode'], 'product_name': data['Артикул'],
#                 'product_width': data['Packing.Ширина'], 'product_units': data['Packing.Name']}
#             await db_manager.upsert_or_insert_data(cur, table, conditions)
#             logger.info(
#                 f'Data for Product with Barcode: "{data['Packing.Barcode']}" was inserted into the "{table}" table '
#                 f'for Warehouse number: "{warehouse_id}" ("{wh_short_name}"). Product Name: '
#                 f'"{conditions["product_name"]}".')
#
#             # Получаем 'product_id' после вставки продукта
#             if cur.lastrowid:
#                 product_id = cur.lastrowid
#             else:
#                 conditions = {'barcode': conditions['barcode']}
#                 result = await db_manager.fetch_with_dict_cursor(table, conditions)
#                 product_id = result[0]['id']
#
#             logger.info(f'Product ID: {product_id}')
#
#             table = 'storage_product'
#             conditions = {
#                 'product_id': product_id, 'warehouse_id': warehouse_id, 'price': data['Packing.Цена'],
#                 'quantity': data['Packing.Колво']}
#             await db_manager.upsert_or_insert_data(cur, table, conditions)
#             logger.info(
#                 f'Data for Product ID: "{product_id}" was inserted into the "{table}" table for Warehouse number: '
#                 f'"{warehouse_id}" ("{wh_short_name}"). Product Price: "{conditions["price"]}"; '
#                 f'Product Quantity: "{conditions["quantity"]}".')
#
#             if keys['storage_location'] in data and data[keys['storage_location']]:
#                 # Получаем 'storage_product_id'
#                 if cur.lastrowid:
#                     storage_product_id = cur.lastrowid
#                 else:
#                     conditions = {'product_id': product_id, 'warehouse_id': warehouse_id}
#                     result = await db_manager.fetch_with_dict_cursor(table, conditions)
#                     storage_product_id = result[0]['id']
#
#                 logger.info(f'Storage Product ID: {storage_product_id}')
#
#                 table = 'storage_locations'
#                 conditions = {
#                     'storage_product_id': storage_product_id, 'location_name_id': location_name_id}
#                 await db_manager.upsert_or_insert_data(cur, table, conditions)
#                 logger.info(
#                     f'Data for Storage Product ID: "{storage_product_id}" was inserted into the "{table}" table for '
#                     f'Warehouse "{warehouse_id}" ("{wh_short_name}"). Product Location Name: '
#                     f'"{conditions["location_name_id"]}".')
#
#     # Закрытие соединения с базой данных
#     await db_manager.close()
    
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
         'Packing.Ширина': 140.0, 'Packing.Состав': {'Хлопок': 100}, 'Код': '2103202475404', 'Packing.Колво': '6',
         'Packing.Date': '27.11.2024', 'Packing.МестоХранения': ['Vip 4-2'], 'Packing.СвободныйОстаток': '6'},
        {'Артикул': '1/24/1/P', 'Packing.Barcode': '2103204102056', 'Packing.Name': 'м', 'Packing.Цена': '1820',
         'Packing.НоваяЦена': '1820', 'Packing.Скидка': '0', 'Packing.Производитель': 'DIFFUSIONE TESSILE S.R.L.',
         'Packing.СтранаПроизводства': 'Италия', 'Наименование': 'Ткань текстильная',
         'Packing.Организация': 'ООО "Дефиле"',
         'Packing.АдресПроизводителя': 'Адрес: 42025 Carviago (RE)-Via Santi, 8-Z.I. Corte Tegge',
         'Packing.Ширина': 139.0, 'Packing.Состав': {'АЦЕТАТ': 67, 'Шелк': 33}, 'Код': '2103204102056',
         'Packing.Колво': '7', 'Packing.Date': '27.11.2024', 'Packing.МестоХранения': ['К 6'],
         'Packing.СвободныйОстаток': '7'},
        {'Артикул': 'PV3', 'Packing.Barcode': '2103202294647', 'Packing.Name': 'м', 'Packing.Цена': '110',
         'Packing.НоваяЦена': '110', 'Packing.Скидка': '0', 'Packing.Производитель': '_',
         'Packing.СтранаПроизводства': 'Китай', 'Наименование': 'Принтер', 'Packing.Организация': 'ООО "Дефиле"',
         'Packing.АдресПроизводителя': '', 'Packing.Ширина': None, 'Packing.Состав': None, 'Код': '2103202294647',
         'Packing.Колво': '1', 'Packing.Date': '27.11.2024', 'Packing.МестоХранения': None,
         'Packing.СвободныйОстаток': '1'}
    ]

    aio_run(update_data(shop_id, valid_records))
    
    shop_id = 'IZH-01'
    valid_records = [
        {'Артикул': '(01/16)', 'Packing.Barcode': '2103402942740', 'Packing.Name': 'м', 'Packing.Цена': '1795',
         'Packing.НоваяЦена': '1795', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Ижтекс"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': {'Шелк': 100}, 'Packing.Плотность': '0', 'Код': '2103402942740',
         'Packing.Колво': '14.4', 'Packing.Date': '11.12.2024', 'Packing.МестоХранения': ['Б2'],
         'Packing.СвободныйОстаток': '14.4', 'Description': 'Ширина 135 см', 'AdditionalDescription': 'Шелк 100%'},
        {'Артикул': 'Шелк сток(05/17)', 'Packing.Barcode': '2103403041077', 'Packing.Name': 'м', 'Packing.Цена': '2465',
         'Packing.НоваяЦена': '2465', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Ижтекс"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': {'Шелк': 100}, 'Packing.Плотность': '0', 'Код': '2103403041077',
         'Packing.Колво': '10', 'Packing.Date': '11.12.2024', 'Packing.МестоХранения': ['Б2'],
         'Packing.СвободныйОстаток': '10', 'Description': 'Ширина 130 см', 'AdditionalDescription': 'Шелк 100%'},
        {'Артикул': '(12/18)', 'Packing.Barcode': '2103403139002', 'Packing.Name': 'м', 'Packing.Цена': '1795',
         'Packing.НоваяЦена': '1795', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Ижтекс"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': {'Шелк': 100}, 'Packing.Плотность': '0', 'Код': '2103403139002',
         'Packing.Колво': '10', 'Packing.Date': '11.12.2024', 'Packing.МестоХранения': ['Б2'],
         'Packing.СвободныйОстаток': '10', 'Description': 'Ширина 135 см, купон 69 см',
         'AdditionalDescription': 'Шелк 100%'}
    ]

    aio_run(update_data(shop_id, valid_records))
    
    shop_id = 'OMS-01'
    valid_records = [
        {'Артикул': '14460/0220', 'Packing.Barcode': '2104910000047', 'Packing.Name': 'м', 'Packing.Цена': '1040',
         'Packing.НоваяЦена': '1040', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': {'Шерсть': 50, 'Полиэстер': 50}, 'Packing.Плотность': '0',
         'Код': '2104910000047', 'Packing.Колво': '8.5', 'Packing.Date': '12.12.2024',
         'Packing.МестоХранения': ['о3', 'о2'], 'Packing.СвободныйОстаток': '8.5', 'Description': 'Ширина 135  см',
         'AdditionalDescription': 'Шерсть 50%  П/Э 50%'},
        {'Артикул': '6/24/1/INK', 'Packing.Barcode': '2103204284936', 'Packing.Name': 'м', 'Packing.Цена': '4710',
         'Packing.НоваяЦена': '4710', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'TWINS S.A.S di Pacciolla Marina & C.', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'VIA VARESINA, 3 - 22075 LURATE CACCIVIO (CO), Италия', 'Packing.Ширина': 140.0,
         'Packing.Состав': {'Шерсть': 70, 'Шелк': 30}, 'Packing.Плотность': '0', 'Код': '2103204284936',
         'Packing.Колво': '7', 'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['84в', '84в'],
         'Packing.СвободныйОстаток': '7', 'Description': 'Ширина 138 см',
         'AdditionalDescription': '70% Шерсть, 30% Шелк'},
        {'Артикул': '78/22/1/ПД', 'Packing.Barcode': '2103202511959', 'Packing.Name': 'м', 'Packing.Цена': '450',
         'Packing.НоваяЦена': '450', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'ITALIAN STOCK FASHION S.R.l.', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'Via Archimede, 233/2 41019 Limidi diSoliera (МO)', 'Packing.Ширина': None,
         'Packing.Состав': {'Вискоза': 85, 'Люрекс': 10, 'Эластан': 5}, 'Packing.Плотность': '0',
         'Код': '2103202511959',
         'Packing.Колво': '32.65', 'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['ст2', 'ст2'],
         'Packing.СвободныйОстаток': '32.65', 'Description': 'Ширина 145 см',
         'AdditionalDescription': 'Вискоза 85% Люрекс 10% Эластан 5%'},
        {'Артикул': 'Punto Milano #11 /24/1/P', 'Packing.Barcode': '2103204408820', 'Packing.Name': 'м',
         'Packing.Цена': '3490', 'Packing.НоваяЦена': '3490', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'VERIAN DI NUTI TOMAS', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'Италия, 59100 Prato, Italy - Via dei Palli, 8 a/5', 'Packing.Ширина': 150.0,
         'Packing.Состав': {'Шерсть': 97, 'Эластан': 3}, 'Packing.Плотность': '0', 'Код': '2103204408820',
         'Packing.Колво': '7.1', 'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['71б', '71б'],
         'Packing.СвободныйОстаток': '7.1', 'Description': 'Ширина 155 см',
         'AdditionalDescription': '97% Шерсть, 3% Эластан'},
        {'Артикул': 'JTC-5012 #16-3803 /19/2/C', 'Packing.Barcode': '2103200416737', 'Packing.Name': 'м',
         'Packing.Цена': '480', 'Packing.НоваяЦена': '480', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'DA.DO. S.r.l', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'Via Tommaso Pini 7/9-59100-Prato (PO) Италия', 'Packing.Ширина': None,
         'Packing.Состав': {'Полиэстер': 98.0, 'Эластан': 2.0}, 'Packing.Плотность': '0', 'Код': '2103200416737',
         'Packing.Колво': '6.5', 'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['42а'],
         'Packing.СвободныйОстаток': '6.5', 'Description': 'Ширина 140 см.',
         'AdditionalDescription': 'П/Э 98%, ЭЛАСТАН 2%'},
        {'Артикул': '2072/22/2/VER', 'Packing.Barcode': '2103203216754', 'Packing.Name': 'м', 'Packing.Цена': '560',
         'Packing.НоваяЦена': '560', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'VERIAN TESSUTI A STOCK', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Текстильный Дом"',
         'Packing.АдресПроизводителя': 'Via dei Palli, 8, 59100 Prato, PO, Италия', 'Packing.Ширина': None,
         'Packing.Состав': {'Вискоза': 100.0}, 'Packing.Плотность': '0', 'Код': '2103203216754', 'Packing.Колво': '3.5',
         'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['72б'], 'Packing.СвободныйОстаток': '3.5',
         'Description': 'Ширина 150см', 'AdditionalDescription': 'ВИСКОЗА 100 %'}
    ]

    aio_run(update_data(shop_id, valid_records))
    
    shop_id = 'BRN-01'
    valid_records = [
        {'Артикул': '11103/0321/LIS', 'Packing.Barcode': '2103202049667', 'Packing.Name': 'м', 'Packing.Цена': '900',
         'Packing.НоваяЦена': '900', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'LISA Spa', 'Packing.СтранаПроизводства': 'Италия', 'Наименование': 'СОРОЧЕЧНАЯ',
         'Packing.Организация': 'ООО "Мода Персона"',
         'Packing.АдресПроизводителя': 'Адрес: Via per Fenegro 26, 22070 VENIANO (CO) ITALY', 'Packing.Ширина': None,
         'Packing.Состав': {'Хлопок': 100}, 'Packing.Плотность': '0', 'Код': '2103202049667', 'Packing.Колво': '9.4',
         'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['А-3', 'БРАК'], 'Packing.СвободныйОстаток': '9.4',
         'Description': 'Ширина 140 см', 'AdditionalDescription': 'Хлопок 100%'},
        {'Артикул': '7483/080118/2', 'Packing.Barcode': '2100200447853', 'Packing.Name': 'м', 'Packing.Цена': '1745',
         'Packing.НоваяЦена': '1745', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Мода Персона"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': {'Полиамид': 30, 'Полиэстер': 55, 'Люрекс': 15}, 'Packing.Плотность': '0',
         'Код': '2100200447853', 'Packing.Колво': '1.3', 'Packing.Date': '12.12.2024',
         'Packing.МестоХранения': ['А-4', 'БРАК'], 'Packing.СвободныйОстаток': '1.3', 'Description': 'Ширина 140 см',
         'AdditionalDescription': 'П/А 30% П/Э 55% Люрекс 15%'},
        {'Артикул': 'TC7584/R1 #17271/24/1/Riopele', 'Packing.Barcode': '2103204344371', 'Packing.Name': 'м',
         'Packing.Цена': '1560', 'Packing.НоваяЦена': '1560', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'Riopele - Texteis, S.A.', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "От-кутюр"',
         'Packing.АдресПроизводителя': 'Av. da Riopele 946, 4770-405 Pousada de Saramagos - Vila Nova de Famalicao, Португалия',
         'Packing.Ширина': 140.0, 'Packing.Состав': {'Полиэстер': 71, 'Вискоза': 27, 'Эластан': 2}, 'Packing.Плотность': '0',
         'Код': '2103204344371', 'Packing.Колво': '7.9', 'Packing.Date': '27.11.2024',
         'Packing.МестоХранения': ['И 4', '8'], 'Packing.СвободныйОстаток': '7.9', 'Description': 'Ширина 140 см',
         'AdditionalDescription': {'Полиэстер': 71, 'Вискоза': 27, 'Эластан': 2}},
        {'Артикул': '864/22/1/C', 'Packing.Barcode': '2103202697844', 'Packing.Name': 'м', 'Packing.Цена': '790',
         'Packing.НоваяЦена': '790', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'DA.DO. S.r.l', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "От-кутюр"',
         'Packing.АдресПроизводителя': 'Via Tommaso Pini 7/9-59100-Prato (PO) Италия', 'Packing.Ширина': None,
         'Packing.Состав': {'Хлопок': 100}, 'Packing.Плотность': '0', 'Код': '2103202697844', 'Packing.Колво': '4.05',
         'Packing.Date': '27.11.2024', 'Packing.МестоХранения': ['А 13', '14'], 'Packing.СвободныйОстаток': '4.05',
         'Description': 'Ширина 150 см', 'AdditionalDescription': 'Хлопок 100%'},
        {'Артикул': '2072/22/2/VER', 'Packing.Barcode': '2103203216754', 'Packing.Name': 'м', 'Packing.Цена': '560',
         'Packing.НоваяЦена': '560', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'VERIAN TESSUTI A STOCK', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "От-кутюр"',
         'Packing.АдресПроизводителя': 'Via dei Palli, 8, 59100 Prato, PO, Италия', 'Packing.Ширина': None,
         'Packing.Состав': {'Вискоза': 97, 'Эластан': 3}, 'Packing.Плотность': '0', 'Код': '2103203216754',
         'Packing.Колво': '7.3', 'Packing.Date': '27.11.2024', 'Packing.МестоХранения': ['А 8', '9'],
         'Packing.СвободныйОстаток': '7.3', 'Description': 'Ширина 150см',
         'AdditionalDescription': 'Вискоза 97%     Эластан 3%'},
        {'Артикул': 'D84409 V.3 (12/18)', 'Packing.Barcode': '2103403136841', 'Packing.Name': 'м',
         'Packing.Цена': '4035', 'Packing.НоваяЦена': '4035', 'Packing.Скидка': '0', 'Packing.СрокАкции': '',
         'Packing.Производитель': 'GOLDEN GROUP srl', 'Packing.СтранаПроизводства': 'Италия',
         'Наименование': 'Ткань текстильная', 'Packing.Организация': 'ООО "Ткани"',
         'Packing.АдресПроизводителя': 'STRADA BULUMINA N.3 LOC. LA CIARULLA - 47899 SERRAVALLE REP. SAN MARINO',
         'Packing.Ширина': None, 'Packing.Состав': None, 'Packing.Плотность': '0', 'Код': '2103403136841',
         'Packing.Колво': '6', 'Packing.Date': '12.12.2024', 'Packing.МестоХранения': ['Ф-1'],
         'Packing.СвободныйОстаток': '6', 'Description': '', 'AdditionalDescription': ''}
    ]

    aio_run(update_data(shop_id, valid_records))
