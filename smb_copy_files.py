__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2025/01/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.8.3'

from typing import Dict, Union
from pathlib import Path
from asyncio import run as aio_run, sleep as aio_sleep
from time import time

from smb_handler import SmbHandler
from logger import logging, setup_logger  # импортируем наш модуль с настройками логгера

setup_logger()
logger = logging.getLogger(__name__)


async def run_smb_copy(config: Dict[str, Union[str, bool]]) -> Union[str, bool]:
    """
    Асинхронно копирует файлы с SMB-сервера на локальную машину.

    Args:
        config (Dict[str, Union[str, bool]]): Словарь с параметрами конфигурации, включающий:
            - 'host': адрес хоста SMB-сервера (str),
            - 'username': имя пользователя для аутентификации (str),
            - 'password': пароль для аутентификации (str),
            - 'share': название сетевой шары (str),
            - 'remote_path': удаленный путь к файлам (str),
            - 'file_pattern': шаблон для поиска файлов (str),
            - 'download_path': локальный путь для сохранения файлов (str),
            - 'download_file_name': имя файла для сохранения (str).

    Returns:
        Union[str, bool]: Путь к загруженному файлу в случае успеха или False, если сервер недоступен.
    """
    smb_handler = SmbHandler(config)

    if await smb_handler.connect_and_prepare():
        if await smb_handler.connect():
            # # ver.: 2.9.0
            # TODO: Требуется добавить имя файла на удаленном сервере (полученное по шаблону)
            # if await smb_handler.file_has_been_updated():
            #     logger.info(f'The file {config['download_file_name']} has been updated on the server.')
            # else:
            #     logger.info(f'No update detected for {config['download_file_name']}.')
            #
            #     file_path = await smb_handler.copy_files()
            #     await smb_handler.disconnect()
            #     return file_path

            file_path = await smb_handler.copy_files()
            await smb_handler.disconnect()
            return file_path
    
    else:
        logger.warning(f'Хост: {config['host']} - недоступен.')
        return False


# Запуск асинхронного скрипта
if __name__ == "__main__":
    from config import get_smb_config, get_schedule_config
    
    
    async def test_run_smb_copy():
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
                
                smb_config = {'host': hostname, 'username': env['user'], 'password': env['password'],
                    'share': env['share'], 'remote_path': env['smb_path'], 'file_pattern': env['file_pattern'],
                    'download_path': env['to_path'] + '-async',
                    'download_file_name': shop_id + Path(env['file_pattern']).suffix, # 'download_file_name': shop_id,
                    # 'multiple': env['multiple']
                }
                
                await run_smb_copy(smb_config)
            
            end_time = time()
            i += 1
            print(f'Время выполнения цикла {i}: {end_time - start_time} секунд.')
            print(f'Пауза на: {check_interval} секунд')
            await aio_sleep(check_interval)
    
    
    aio_run(test_run_smb_copy())
