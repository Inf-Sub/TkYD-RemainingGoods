__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/13'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.2.5'

from typing import Union
from os import getenv, sep as os_sep
from os.path import join, exists
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
from app.config import REPO_DIR
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


async def copy_files(
        network_path: str, file_pattern: str, download_path: str, download_file_name: str, multiple: bool = False
) -> Union[str, bool]:
    await make_dir(download_path)
    hostname = network_path.split(os_sep)[2]
    combined_file_path = join(
        download_path, download_file_name + (Path(file_pattern).suffix if multiple else Path(file_pattern).suffix))

    try:
        dir_entries = listdir(network_path)

        async with aio_open(combined_file_path, mode='wb') as dest_file:
            for entry in dir_entries:
                if fnmatch(entry, file_pattern):
                    src_file_path = join(network_path, entry)

                    logger.info(f'{hostname}\tCopying "{entry}" to "{Path(combined_file_path).name}"')

                    try:
                        # TODO: корректно не работает с aiofiles.open() в данной части кода, причины не ясны, временно
                        #  оставлен синхронный вариант через smbclient.open_file()
                        # with aio_open(src_file_path, mode='rb') as src_file:  # not read remote file
                        with open_file(src_file_path, mode='rb') as src_file:
                            while chunk := src_file.read(4096):
                                await dest_file.write(chunk)
                    except Exception as e:
                        logger.error(f'{hostname}\tError copying file: {src_file_path}: {e}')
                        return False

            logger.info(f'{hostname}\tCopying complete.')
        return combined_file_path

    except Exception as e:
        logger.error(f'{hostname}\tError accessing {network_path}: {e}')
        return False


class SmbHandler:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    async def connect(self, network_path: str) -> bool:
        ClientConfig(username=self.username, password=self.password)
        try:
            listdir(network_path)  # Проверка доступа
            return True
        except Exception as e:
            logger.error(f'Ошибка при подключении к {network_path}: {e}')
            return False


async def run(
        server: str, share: str, path: str, username: str, password: str, file_pattern: str, download_path: str,
        download_file_name: str) -> Union[str, bool]:
    if await async_ping(server):
        logger.info(f'Хост: {server} - доступен. Подключение к сетевой шаре {share} ...')
        network_path = await create_network_path_async(server=server, share=share, path=path)

        smb_handler = SmbHandler(username, password)

        if await smb_handler.connect(network_path):
            # return await copy_many_files(
            #     network_path=network_path, file_pattern=file_pattern, download_path=download_path,
            #     download_file_name=download_file_name)
            return await copy_files(
                network_path=network_path, file_pattern=file_pattern, download_path=download_path,
                download_file_name=download_file_name
            )

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
    SMB_PATH = getenv('SMB_PATH')
    SMB_USERNAME = getenv('SMB_USERNAME')
    SMB_PASSWORD = getenv('SMB_PASSWORD')
    LOAD_TO_PATH = join(REPO_DIR, getenv('LOAD_TO_PATH')) + '-async'
    LOAD_FILE_PATTERN = getenv('LOAD_FILE_PATTERN')
    SMB_SLEEP_INTERVAL = int(getenv('SMB_SLEEP_INTERVAL'))


    async def test_run():
        i = 0
        while True:
            start_time = time()

            for shop_id in SHOPS:
                hostname = SMB_HOSTNAME_TEMPLATE.format(shop_id)
                # print(f'test_run:\t{hostname}')

                if await async_ping(hostname):
                    print(f'test_run:\tХост: {hostname} - доступен. Подключение к сетевой шаре...')

                    await run(
                        server=hostname, share=SMB_SHARE, path=SMB_PATH, username=SMB_USERNAME, password=SMB_PASSWORD,
                        file_pattern=LOAD_FILE_PATTERN, download_path=LOAD_TO_PATH, download_file_name=shop_id
                    )

                else:
                    print(f'test_run:\tХост: {hostname} - недоступен.')

            end_time = time()
            i += 1
            print(f'Время выполнения цикла {i}: {end_time - start_time} секунд.')
            print(f'Пауза на: {SMB_SLEEP_INTERVAL} секунд')
            await sleep(SMB_SLEEP_INTERVAL)


    async_run(test_run())
