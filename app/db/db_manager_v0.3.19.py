__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/06'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '0.3.19'


import asyncio
import aiomysql
import json

from app.utils.logging_config import logging, setup_logging


setup_logging()
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    async def connect(self, loop):
        try:
            self.conn = await aiomysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,  # исправлено: добавлен параметр database для выбора текущей базы данных
                loop=loop
            )
            logger.info('Соединение с сервером MySQL установлено.')
        except aiomysql.Error as e:
            logger.error(f'Ошибка подключения к MySQL: {e}')

    async def check_and_create_database(self):
        async with self.conn.cursor() as cur:
            await cur.execute(f"SHOW DATABASES LIKE '{self.database}'")
            database_exists = await cur.fetchone()

            if not database_exists:
                logger.info('База данных не существует или у вас нет необходимых прав.')
                return False
            await cur.execute(f"USE {self.database}")
            return True

    async def create_tables(self):
        async with self.conn.cursor() as cur:
            # Проверяем существование таблицы
            table = 'cities'

            await cur.execute(f"SHOW TABLES LIKE '{table}';")
            result = await cur.fetchone()

            if result:
                print(f"Таблица '{table}' существует.")
            else:
                print(f"Таблица '{table}' не найдена.")

                await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TINYINT(2) NOT NULL AUTO_INCREMENT,
                    city_name VARCHAR(15) NOT NULL,
                    PRIMARY KEY (id) USING BTREE,
                    UNIQUE INDEX city_name (city_name)
                )
                """)
                logger.info(f"Таблица '{table}' создана.")

            # Заполнить таблицу из файла
            await self.initialize_data_cities(DB_INIT_DATA_CITIES_PATH)

            # Проверяем существование таблицы
            table = 'stores'

            await cur.execute(f"SHOW TABLES LIKE '{table}';")
            result = await cur.fetchone()

            if result:
                print(f"Таблица '{table}' существует.")
            else:
                print(f"Таблица '{table}' не найдена.")

                await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TINYINT(2) NOT NULL AUTO_INCREMENT,
                    identity CHAR(6) NOT NULL,
                    city VARCHAR(15) NULL DEFAULT NULL,
                    address VARCHAR(100) NULL DEFAULT NULL,
                    update_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE INDEX identity (identity),
                    CONSTRAINT FK_stores_cities FOREIGN KEY (city) REFERENCES cities (city_name)
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
                """)
                logger.info(f"Таблица '{table}' создана.")

            # Заполнить таблицу из файла
            await self.initialize_data_stores(DB_INIT_DATA_STORES_PATH)

            # Проверяем существование таблицы
            table = 'employees'

            await cur.execute(f"SHOW TABLES LIKE '{table}';")
            result = await cur.fetchone()

            if result:
                print(f"Таблица '{table}' существует.")
            else:
                print(f"Таблица '{table}' не найдена.")

                await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id INT(4) NOT NULL AUTO_INCREMENT,
                    app_user_id BIGINT(12) UNSIGNED ZEROFILL NOT NULL,
                    app_user_login VARCHAR(20) NULL DEFAULT NULL,
                    store_id CHAR(6) NOT NULL,
                    last_name VARCHAR(20) NULL DEFAULT NULL,
                    first_name VARCHAR(20) NULL DEFAULT NULL,
                    middle_name VARCHAR(20) NULL DEFAULT NULL,
                    birthday DATE NULL DEFAULT NULL,
                    position ENUM('Director','Top manager','Manager','Cashier','Storekeeper') NULL DEFAULT 'Manager',
                    status ENUM('working','fired') NOT NULL DEFAULT 'working',
                    hired DATE NULL DEFAULT NULL COMMENT 'Принят на работу',
                    dismissal_date DATE NULL DEFAULT NULL COMMENT 'Дата увольнения',
                    passport_series SMALLINT(4) NULL DEFAULT NULL COMMENT 'Серия паспорта',
                    passport_number MEDIUMINT(6) NULL DEFAULT NULL COMMENT 'Номер паспорта',
                    TIN MEDIUMINT(6) NULL DEFAULT NULL COMMENT 'ИНН',
                    created_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    update_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE INDEX app_user_id (app_user_id),
                    INDEX FK_employees_stores (store_id),
                    CONSTRAINT FK_employees_stores FOREIGN KEY (store_id) REFERENCES stores (identity) 
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
                COMMENT='Сотрудники'
                """)
                logger.info(f"Таблица '{table}' создана.")
                
            # Проверяем существование таблицы
            table = 'store_hours'

            await cur.execute(f"SHOW TABLES LIKE '{table}';")
            result = await cur.fetchone()

            if result:
                print(f"Таблица '{table}' существует.")
            else:
                print(f"Таблица '{table}' не найдена.")

                await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TINYINT(2) NOT NULL AUTO_INCREMENT,
                    store_id CHAR(6) NOT NULL,
                    # week_days SET('Mon','Tue','Wed','Thu','Fri','Sat','Sun') NOT NULL 
                    #     DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
                    week_days ENUM('weekdays','weekends') NOT NULL DEFAULT 'weekdays',
                    opening_time TIME NULL DEFAULT '09:00:00',
                    closing_time TIME NULL DEFAULT '19:00:00',
                    update_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    UNIQUE INDEX `store_id_week_days` (`store_id`, `week_days`),
                    INDEX FK_store_hours_stores (store_id),
                    CONSTRAINT FK_store_hours_stores FOREIGN KEY (store_id) REFERENCES stores (identity) 
                        ON UPDATE CASCADE ON DELETE RESTRICT
                )
                COMMENT='Часы работы магазинов'
                """)
                logger.info(f"Таблица '{table}' создана.")

    async def initialize_data_cities(self, json_data_path: str) -> None:
        # Загружаем данные из JSON
        print(f'Загружаем данные из JSON: {json_data_path}')
        with open(json_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        table = 'stores'
        for entry in data:
            print(entry)
            city = entry['city']
            print(city)

            await self.insert_or_update_city(city)

        await self.conn.commit()
        logger.info(f"Таблица '{table}' инициализирована данными из файла.")

    async def initialize_data_stores(self, json_data_path: str) -> None:
        # Загружаем данные из JSON
        print(f'Загружаем данные из JSON: {json_data_path}')
        with open(json_data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        table = 'stores'
        for entry in data:
            identity = entry['identity']
            city = entry['city']
            address = entry['address']

            await self.insert_or_update_store(identity, city, address)

        await self.conn.commit()
        logger.info(f"Таблица '{table}' инициализирована данными из файла.")

    async def insert_or_update_city(self, city_name):
        async with self.conn.cursor() as cur:
            table = 'cities'

            await cur.execute(f"""
                INSERT INTO {table} (city_name) 
                VALUES (%s)
                ON DUPLICATE KEY UPDATE 
                city_name = VALUES(city_name)
            """, (city_name, ))

            await self.conn.commit()
            logger.info(f"Данные в таблице '{table}' обновлены или добавлены для: {city_name}")

    async def insert_or_update_store(self, identity, city, address):
        async with self.conn.cursor() as cur:
            table = 'stores'

            await cur.execute(f"""
                INSERT INTO {table} (identity, city, address) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                city = VALUES(city), 
                address = VALUES(address)
            """, (identity, city, address))
            await self.conn.commit()
            logger.info(f"Данные в таблице '{table}' обновлены или добавлены для: {identity}")

    async def insert_or_update_employee(self, app_user_id, app_user_login, store_id):
        async with self.conn.cursor() as cur:
            table = 'employees'

            # Если переменная будет пустой строкой или None
            # status = status if status else None

            await cur.execute(f"""
                INSERT INTO {table} (app_user_id, app_user_login, store_id)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                app_user_id = VALUES(app_user_id),
                app_user_login = VALUES(app_user_login),
                store_id = VALUES(store_id),
                update_date = CURRENT_TIMESTAMP
            """, (app_user_id, app_user_login, store_id))
            await self.conn.commit()
            logger.info(f"Данные в таблице '{table}' обновлены или добавлены для: {store_id}: {app_user_login}")

    async def insert_or_update_store_hours(self, store_id, week_days, opening_time, closing_time):
        async with self.conn.cursor() as cur:
            table = 'store_hours'

            await cur.execute(f"""
                INSERT INTO {table} (store_id, week_days, opening_time, closing_time)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                store_id = VALUES(store_id),
                week_days = VALUES(week_days),
                opening_time = VALUES(opening_time),
                closing_time = VALUES(closing_time)
            """, (store_id, week_days, opening_time, closing_time))
            await self.conn.commit()
            logger.info(f"Данные в таблице '{table}' обновлены или добавлены для: {store_id}")

    async def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Соединение с сервером MySQL закрыто.")


async def main():
    loop = asyncio.get_event_loop()
    db_manager = DatabaseManager(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USERNAME, password=DB_PASSWORD)

    await db_manager.connect(loop)

    if await db_manager.check_and_create_database():
        await db_manager.create_tables()

        # Примеры добавления или обновления данных
        # store
        await db_manager.insert_or_update_store(
            identity='MSK-01', city='Москва', address='ул. Автозаводская, 9')
        await db_manager.insert_or_update_store(
            identity='MSK-02', city='Москва', address='Ленинский проспект, 39/1')
        await db_manager.insert_or_update_store(
            identity='MSK-03', city='Москва', address='Ленинский проспект, 31/1, стр. 1')

        # employee
        await db_manager.insert_or_update_employee(
            app_user_id='054400000025', app_user_login='wewe', store_id='MSK-03')
        await db_manager.insert_or_update_employee(
            app_user_id='054400000043', app_user_login='vxcvc', store_id='MSK-03')
        await db_manager.insert_or_update_employee(
            app_user_id='054400000001', app_user_login='vcs', store_id='MSK-03')
        await db_manager.insert_or_update_employee(
            app_user_id='006400000064', app_user_login='Бадалян', store_id='EKB-01')
        await db_manager.insert_or_update_employee(
            app_user_id='006400000185', app_user_login='Максимова', store_id='EKB-01')
        await db_manager.insert_or_update_employee(
            app_user_id='006400000166', app_user_login='Семенова', store_id='EKB-01')
        await db_manager.insert_or_update_employee(
            app_user_id='006400000189', app_user_login='Алексеева', store_id='EKB-01')
        
        # store_hours
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-01', week_days='weekdays', opening_time='09:00:00', closing_time='20:00:00')
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-01', week_days='weekends', opening_time='11:00:00', closing_time='21:00:00')
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-02', week_days='weekdays', opening_time='09:00:00', closing_time='19:00:00')
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-02', week_days='weekends', opening_time='09:00:00', closing_time='19:00:00')
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-03', week_days='weekdays', opening_time='09:00:00', closing_time='21:00:00')
        await db_manager.insert_or_update_store_hours(
            store_id='MSK-03', week_days='weekends', opening_time='09:00:00', closing_time='21:00:00')

    await db_manager.close()


if __name__ == '__main__':
    from os.path import join
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

    DB_INIT_DATA_CITIES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_CITIES_FILE_PATH'))
    DB_INIT_DATA_STORES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_STORES_FILE_PATH'))

    asyncio.run(main())
