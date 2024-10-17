__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/14'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '2.2.6'


from asyncio import run as async_run, sleep, create_task, gather
from os import getenv
from os.path import join
from time import time
from datetime import datetime as dt
from dotenv import load_dotenv

from app.parse.log_parser import run as parse_log
from app.utils.logging_config import logging, setup_logging
from app.config import REPO_DIR, DATA_DIR
from app.smb.smb_files import run as smb_run
from app.utils.convert_charset import convert_to_utf8
from app.utils.server_status import update_server_status

# Загрузка переменных из .env файла
load_dotenv()


SHOPS = getenv('SHOPS').replace(' ', '').split(',')

SMB_HOSTNAME_TEMPLATE = getenv('SMB_HOSTNAME_TEMPLATE')
SMB_SHARE = getenv('SMB_SHARE')
SMB_PATH = getenv('SMB_PATH')
SMB_USERNAME = getenv('SMB_USERNAME')
SMB_PASSWORD = getenv('SMB_PASSWORD')

LOAD_TO_PATH = join(REPO_DIR, getenv('LOAD_TO_PATH'))
LOAD_FILE_PATTERN = getenv('LOAD_FILE_PATTERN')
FIND_TEXT_PATTERN = getenv('FIND_TEXT_PATTERN')
SMB_SLEEP_INTERVAL = int(getenv('SMB_SLEEP_INTERVAL'))

DB_HOST = getenv('DB_HOST')
DB_PORT = int(getenv('DB_PORT'))
DB_NAME = getenv('DB_NAME')
DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')

# DB_INIT_DATA_CITIES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_CITIES_FILE_PATH'))
# DB_INIT_DATA_STORES_PATH = join(DATA_DIR, getenv('DB_INIT_DATA_STORES_FILE_PATH'))
DB_INIT_SCHEMAS = getenv('DB_INIT_SCHEMAS')


async def ln(num: int = 30) -> str:
    return f'\n{"=" * num}'


async def perform_smb_task(shop_id: str, pattern: str) -> None:
    hostname = SMB_HOSTNAME_TEMPLATE.format(shop_id)
    start_connect_time = time()

    try:
        log_file_path = await smb_run(
            server=hostname, share=SMB_SHARE, path=SMB_PATH, username=SMB_USERNAME, password=SMB_PASSWORD,
            file_pattern=LOAD_FILE_PATTERN, download_path=LOAD_TO_PATH, download_file_name=shop_id
        )

        logging.getLogger(__name__).debug(f'Время подключения к "{hostname}": {time() - start_connect_time} секунд.')

        if log_file_path is not False:
            await convert_to_utf8(log_file_path)  # Convert file to UTF-8 if needed
            await parse_log(log_file_path, pattern)

        # Обновить статус сервера
        await update_server_status(hostname, log_file_path)

    except Exception as e:
        logging.getLogger(__name__).error(f'Ошибка при обработке магазина {shop_id}: {e}')
        # Обновить статус сервера при ошибке
        await update_server_status(hostname, False)


# async def process_file(file: str, pattern: str):
#     await convert_to_utf8(file)  # Convert file to UTF-8 if needed
#     await parse_log(file, pattern)


async def run():
    now = dt.now()
    formatted_date_time = now.strftime('on %Y.%m.%d at %H:%M')

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f'Скрипт запущен в {formatted_date_time}.')

    while True:
        start_cycle_time = time()

        tasks = [create_task(perform_smb_task(shop_id, FIND_TEXT_PATTERN)) for shop_id in SHOPS]
        # Ждем завершения всех задач
        await gather(*tasks)

        # tasks = [create_task(process_file(join(LOG_SMP_PATH, f'{shop_id}.log'))) for shop_id in SHOPS]
        # # Ждем завершения всех задач
        # await gather(*tasks)

        logger.info(f'Время выполнения цикла: {time() - start_cycle_time} секунд.')
        logger.info(f'Пауза на: {SMB_SLEEP_INTERVAL} секунд')
        await sleep(SMB_SLEEP_INTERVAL)


if __name__ == '__main__':
    async_run(run())
