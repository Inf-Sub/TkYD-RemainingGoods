__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2025/01/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '2.8.3'

from asyncio import run as aio_run, sleep as aio_sleep, create_task as aio_create_task, gather as aio_gather
# from asyncio import get_event_loop as aio_get_event_loop
# from pprint import pprint
from typing import Dict, List, Any, Optional, Union
from time import time
from datetime import datetime as dt
from pathlib import Path
from logger import logging, setup_logger
from config import get_smb_config, get_schedule_config
from smb_copy_files import run_smb_copy
from csv_validator import CSVValidator
from db import update_data
# from convert_charset import convert_encoding
from server_status import AsyncKeyValueStore
# import inspect

setup_logger()
logger = logging.getLogger(__name__)


async def ln(num: int = 30) -> str:
    """
    Возвращает строку, состоящую из символов '='.

    :param num: (optional): Количество символов '=' в строке. По умолчанию равно 30.

    :return: Строка, начинающаяся с новой строки, за которой следуют символы '=' в количестве, указанном в параметре num.
    """
    return f'\n{'=' * num}'



async def perform_smb_task(srv_status: AsyncKeyValueStore, shop_id: str) -> None:
    """
    Выполняет задачу получения файла по протоколу SMB и его последующей обработки.

    :param srv_status: Экземпляр AsyncKeyValueStore, управляющий статусом сервера.
    :param shop_id: идентификатор магазина
    
    :return: None
    """
    start_connect_time = time()
    env: Dict[str, Any] = get_smb_config()
    debug_mode: bool = env['debug_mode']
    hostname: str = env['host_template'].format(shop_id)
    # Формирование полного пути к файлу для сохранения
    # download_path = os_join(env['to_path'], shop_id + Path(env['file_pattern']).suffix)
    file_path: Optional[str] = None
    valid_records: Optional[List[Dict[str, Any]]] = None
    smb_config: Dict[str, Union[str, bool]] = {
        'host': hostname,
        'port': env['port'],
        'username': env['user'],
        'password': env['password'],
        'share': env['share'],
        'remote_path': env['smb_path'],
        'file_pattern': env['file_pattern'],
        # 'file_pattern': f'{shop_id}-{env['file_pattern']}',
        'download_path': env['to_path'],
        'download_file_name': shop_id + Path(env['file_pattern']).suffix,
        # 'download_file_name': shop_id,
        # 'multiple': env['multiple'],
        'debug_mode': debug_mode,
    }

    try:
        file_path = await run_smb_copy(smb_config)
        logger.warning(
            f'SMBHandler: Время с момента подключения к "{hostname}": {(time() - start_connect_time) / 60:.1f} минут '
            f'({time() - start_connect_time:.2f} секунд).')
        
        if not file_path:
            return

    except IndexError as e:
        logger.error(f'Индекс вышел за пределы диапазона при обработке магазина {shop_id}: {e}')
    except Exception as e:
        if not debug_mode:
            logger.error(f'Ошибка при обработке магазина {shop_id}: {e}')
        else:
            raise
    finally:
        # Обновление статуса сервера
        await srv_status.set_value(hostname, file_path)
        
        logger.warning(f'Обновление статуса сервера: "{hostname}". Статус: "{bool(file_path)}"')


    # print(f'type file_path: {type(file_path)} {file_path}')
    # if not file_path:
    #     logger.warning('The path to the file is missing.')
    # else:
    try:
        handler = CSVValidator()
        valid_records = await handler.process_csv(file_path)
        logger.warning(
            f'CSVValidator: Время с момента подключения к "{hostname}": {(time() - start_connect_time) / 60:.1f} минут '
            f'({time() - start_connect_time:.2f} секунд).')
        if not valid_records:
            logger.warning('Failed to process records.')
            return

        # await run_csv_reader(file_path)
    except Exception as e:
        if not debug_mode:
            logger.error(f'Ошибка при чтении файла магазина {shop_id} в UTF-8: {e}')
        else:
            raise
        
        # print(f'type valid_records: {type(valid_records)} {valid_records}')
        # if not valid_records:
        #     logger.warning('Failed to process records.')
        # else:
        
    try:
        logger.info('Validation successful.')
        # импортируем данные в БД
        await update_data(shop_id, valid_records)
        logger.warning(
            f'DBHandler: Время с момента подключения к "{hostname}": {(time() - start_connect_time) / 60:.1f} минут '
            f'({time() - start_connect_time:.2f} секунд).')
    except Exception as e:
        if not debug_mode:
            logger.error(f'Ошибка при импорте данных в БД для магазина {shop_id}: {e}')
        else:
            raise


async def run() -> None:
    """
    Основная функция для запуска цикла обработки.
    
    :return: None
    """
    now = dt.now()
    formatted_date_time = now.strftime('%Y.%m.%d at %H:%M')

    logger.warning(f'Script launched {formatted_date_time}.')

    srv_status = AsyncKeyValueStore()

    env = get_schedule_config()
    hosts = get_smb_config()['hosts']

    while True:
        start_cycle_time = time()

        tasks = [aio_create_task(perform_smb_task(srv_status, shop_id)) for shop_id in hosts]
        # Ждем завершения всех задач
        await aio_gather(*tasks)

        await srv_status.save_to_file()

        logger.warning(f'Время выполнения цикла: {(time() - start_cycle_time) / 60:.1f} минут '
                       f'({time() - start_cycle_time:.2f} секунд).')
        logger.warning(f'Пауза на: {env["check_interval"]} секунд.')
        await aio_sleep(env['check_interval'])


if __name__ == '__main__':
    try:
        aio_run(run())
    except KeyboardInterrupt:
        logger.warning(f'Программа была остановлена пользователем.')