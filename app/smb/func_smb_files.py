__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/03'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.1.6'


from os import getenv
from os.path import join
from asyncio import run as async_run, sleep, get_event_loop
from aiofiles import open as aio_open
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fnmatch import fnmatch
from dotenv import load_dotenv
from ping3 import ping
from time import time
from smbclient import ClientConfig, listdir, open_file

from app.utils.logging_config import logging, setup_logging  # импортируем наш модуль с настройками логгера
from app.config import REPO_DIR as LOCAL_REPO_DIR
from app.utils.make_dir import make_dir


setup_logging()
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования

# Загрузка переменных из .env файла
load_dotenv()


async def async_ping(host: str) -> bool:
    loop = get_event_loop()
    with ThreadPoolExecutor() as executor:
        response = await loop.run_in_executor(executor, ping, host)
    return bool(response)


async def create_network_path_async(server: str, share: str, path: str = '') -> str:
    if path:
        # Если путь не пустой, добавляем его
        network_path = r'\\{}\{}\{}'.format(server, share, path)
    else:
        # Если путь пустой, игнорируем его
        network_path = r'\\{}\{}'.format(server, share)
    return network_path


async def smb_connection(
        network_path: str, username: str, password: str, file_pattern: str, log_dir: str, log_file: str
) -> str or bool:
    await make_dir(log_dir)

    # Установка учетных данных для доступа к сетевой папке
    ClientConfig(username=username, password=password)

    try:
        dir_entries = listdir(network_path)
        for entry in dir_entries:
            if fnmatch(entry, file_pattern):
                src_file_path = join(network_path, entry)
                dest_file_path = join(log_dir, f'{log_file}{Path(src_file_path).suffix}')

                logger.info(f'From "{src_file_path.split('\\')[2]}" copy "{entry}" to "{Path(dest_file_path).name}"')
        #         # Открываем источник синхронно
        #         with open_file(src_file_path, mode='rb') as src_file:
        #             async with aio_open(dest_file_path, mode='wb') as dest_file:
        #                 while True:
        #                     data = src_file.read(4096)
        #                     if not data:
        #                         break
        #                     await dest_file.write(data)
        #         logger.info(f'Copying complete.')
        #         return dest_file_path
        #
        # return False

                try:
                    with open_file(src_file_path, mode='rb') as src_file:
                        async with aio_open(dest_file_path, mode='wb') as dest_file:
                            while chunk := src_file.read(4096):
                                await dest_file.write(chunk)
                    logger.info('Copying complete.')
                    return dest_file_path
                except Exception as e:
                    logger.error(f'Ошибка при копировании файла: {src_file_path}: {e}')
                    return False

        logger.info('No matching files found.')
        return False

    except Exception as e:
        logger.error(f'Ошибка при доступе к {network_path}: {e}')
        return False


async def run(
        server: str, share: str, path: str, username: str, password: str, file_pattern: str, log_dir: str, log_file: str
) -> str or bool:
    if await async_ping(server):
        logger.info(f'Хост: {server} - доступен. Подключение к сетевой шаре {share} ...')
        dest_file_path = await smb_connection(
            network_path=await create_network_path_async(server=server, share=share, path=path), username=username,
            password=password, file_pattern=file_pattern, log_dir=log_dir, log_file=log_file
        )
        return dest_file_path
    else:
        logger.info(f'Хост: {server} - недоступен.')
        return False


# Запуск асинхронного скрипта
if __name__ == "__main__":
    SHOPS = getenv('SHOPS').replace(' ', '').split(',')
    SMB_HOSTNAME_TEMPLATE = getenv('SMB_HOSTNAME_TEMPLATE')
    # SMB_PORT = int(getenv('SMB_PORT'))
    SMB_TIMEOUT = int(getenv('SMB_TIMEOUT'))
    SMB_SHARE = getenv('SMB_SHARE')
    SMB_USERNAME = getenv('SMB_USERNAME')
    SMB_PASSWORD = getenv('SMB_PASSWORD')
    LOG_SMP_PATH = join(REPO_DIR, getenv('LOG_SMP_PATH')) + '-Full'
    FILE_PATTERN = getenv('LOG_FILE_PATTERN')
    SMB_SLEEP_INTERVAL = int(getenv('SMB_SLEEP_INTERVAL'))


    async def test_run():
        i = 0
        while True:
            start_time = time()

            for shop_id in SHOPS:
                hostname = SMB_HOSTNAME_TEMPLATE.format(shop_id)
                # print(hostname)

                if await async_ping(hostname):
                    print(f'Хост: {hostname} - доступен. Подключение к сетевой шаре...')
                    await smb_connection(
                        network_path=await create_network_path_async(server=hostname, share=SMB_SHARE, path=''),
                        username=SMB_USERNAME, password=SMB_PASSWORD, file_pattern=FILE_PATTERN,
                        log_dir=LOG_SMP_PATH, log_file=shop_id
                    )

                else:
                    print(f'Хост: {hostname} - недоступен.')

            end_time = time()
            i += 1
            print(f'Время выполнения цикла {i}: {end_time - start_time} секунд.')
            print(f'Пауза на: {SMB_SLEEP_INTERVAL} секунд')
            await sleep(SMB_SLEEP_INTERVAL)

    async_run(test_run())


