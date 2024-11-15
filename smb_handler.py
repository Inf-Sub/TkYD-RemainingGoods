__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/16'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.5.0'

# from pprint import pprint
from typing import Dict, Union
# from os import getenv, sep as os_sep
from os.path import join as os_join
from pathlib import Path
from asyncio import run as async_run, sleep, get_event_loop
from aiofiles import open as aio_open
from concurrent.futures import ThreadPoolExecutor
from fnmatch import fnmatch
from ping3 import ping
from time import time
from smbclient import ClientConfig, listdir, open_file
from smbprotocol.exceptions import SMBConnectionClosed

from logger import logging, setup_logger  # импортируем наш модуль с настройками логгера
# from app.config import REPO_DIR
from make_dir import make_dir

setup_logger()
logger = logging.getLogger(__name__)


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
        server: str, network_path: str, file_pattern: str, download_path: str, download_file_name: str
) -> Union[str, bool]:
    """
    server: str  # Имя/hostname SMB сервера
    network_path: str,  # Путь к сетевому ресурсу
    file_pattern: str,  # Шаблон имени файла для поиска
    download_path: str,  # Путь, куда будут скачаны файлы
    download_file_name: str,  # Имя файла, под которым будет сохранён скачанный файл
    multiple: bool = False  # Флаг, указывающий, нужно ли обрабатывать несколько файлов
    return Union[str, bool]:  # Возвращаемое значение: строка (путь к файлу) или булево значение (успех/неудача)
    """

    # Создание директории для загрузки, если она не существует
    await make_dir(os_join(Path.cwd(), download_path))

    # Извлечение имени хоста из сетевого пути
    # server = network_path.split(os_sep)[2]

    # Формирование полного пути к файлу для сохранения
    # file_path = join(
    #     download_path,
    #     download_file_name + (Path(file_pattern).suffix if multiple else Path(file_pattern).suffix)
    # )
    file_path = os_join(download_path, download_file_name)

    try:
        # Получение списка файлов в указанной директории
        dir_entries = listdir(network_path)

        # Открытие файла для записи (асинхронно)
        async with aio_open(file_path, mode='wb') as dest_file:
            for entry in dir_entries:
                # Проверка, соответствует ли имя файла шаблону
                if fnmatch(entry, file_pattern):
                    src_file_path = os_join(network_path, entry)  # Полный путь к исходному файлу

                    logger.info(f'{server}: Copying "{entry}" to "{Path(file_path).name}"')

                    try:
                        # Открытие исходного файла через SMB
                        # Временно используется синхронный вариант из-за проблем с aiofiles
                        with open_file(src_file_path, mode='rb') as src_file:
                            # Чтение и запись файла по частям (chunk)
                            while chunk := src_file.read(4096):
                                await dest_file.write(chunk)

                    except SMBConnectionClosed as e:
                        logger.error(f'{server}: Error copying file: {src_file_path}: {e}')
                        # Здесь можно добавить логику для повторной попытки или отправки уведомления
                        return False  # Возврат False в случае ошибки

                    except Exception as e:
                        logger.error(f'{server}: An unexpected error occurred: {e}')
                        return False  # Возврат False в случае ошибки

            logger.info(f'{server}: Copying complete.')

        return file_path  # Возврат пути к сохранённому файлу

    except Exception as e:
        logger.error(f'{server}: Error accessing {network_path}: {e}')
        return False


class SmbHandler:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.connection = None

    async def connect(self, network_path: str) -> bool:
        ClientConfig(username=self.username, password=self.password)
        try:
            listdir(network_path)  # Проверка доступаself.connection = True  # Устанавливаем флаг соединения
            logger.info(f'Successfully connected to {network_path}')
            return True
        except Exception as e:
            logger.error(f'Error connecting to {network_path}: {e}')
            return False

    async def disconnect(self) -> None:
        if self.connection:  # Проверяем, было ли установлено соединение
            # Здесь может быть логика для завершения соединения
            logger.info('Connection closed')
            self.connection = None
        else:
            logger.warning('Attempt to close non-existent connection')


async def run(config: Dict[str, Union[str, bool]]) -> Union[str, bool]:
    if await async_ping(config['server']):
        logger.info(f'Хост: {config['server']} - доступен. Подключение к сетевой шаре {config['share']} ...')

        config['network_path'] = await create_network_path_async(
            server=config['server'], share=config['share'], path=config['remote_path'])

        smb_handler = SmbHandler(config['username'], config['password'])

        if await smb_handler.connect(config['network_path']):
            # return await copy_many_files(
            #     network_path=network_path, file_pattern=file_pattern, download_path=download_path,
            #     download_file_name=download_file_name)

            # return await copy_files(
            #     server=config['server'], network_path=config['network_path'], file_pattern=config['file_pattern'],
            #     download_path=config['download_path'], download_file_name=config['download_file_name'])

            file_path = await copy_files(
                server=config['server'], network_path=config['network_path'], file_pattern=config['file_pattern'],
                download_path=config['download_path'], download_file_name=config['download_file_name'])
            await smb_handler.disconnect()
            return file_path

    else:
        logger.warning(f'Хост: {config['server']} - недоступен.')
        return False


# Запуск асинхронного скрипта
if __name__ == "__main__":
    from config import get_smb_config, get_schedule_config


    async def test_run():
        i = 0
        while True:
            start_time = time()
            env = get_smb_config()
            check_interval = get_schedule_config()['check_interval']

            for shop_id in env['hosts']:
                """Выполняет задачу получения файла по SMB и его обработки."""
                start_connect_time = time()

                hostname = env['host_template'].format(shop_id)
                # Формирование полного пути к файлу для сохранения
                # download_path = join(env['to_path'], shop_id + Path(env['file_pattern']).suffix)

                smb_config = {
                    'server': hostname,
                    'username': env['user'],
                    'password': env['password'],
                    'share': env['share'],
                    'remote_path': env['smb_path'],
                    'file_pattern': env['file_pattern'],
                    'download_path': env['to_path'] + '-async',
                    'download_file_name': shop_id + Path(env['file_pattern']).suffix,
                    # 'download_file_name': shop_id,
                    # 'multiple': env['multiple']
                }

                if await async_ping(hostname):
                    print(f'test_run:\tХост: {hostname} - доступен. Подключение к сетевой шаре...')

                    await run(smb_config)

                else:
                    print(f'test_run:\tХост: {hostname} - недоступен.')

            end_time = time()
            i += 1
            print(f'Время выполнения цикла {i}: {end_time - start_time} секунд.')
            print(f'Пауза на: {check_interval} секунд')
            await sleep(check_interval)


    async_run(test_run())