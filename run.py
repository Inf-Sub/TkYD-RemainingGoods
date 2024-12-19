__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/18'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Development'  # 'Production / Development'
__version__ = '2.7.5'

from asyncio import run as aio_run, sleep as aio_sleep, create_task as aio_create_task, gather as aio_gather
# from asyncio import get_event_loop as aio_get_event_loop
# from pprint import pprint
from time import time
from datetime import datetime as dt
# from os.path import join as os_join
from pathlib import Path
from logger import logging, setup_logger
from config import get_smb_config, get_schedule_config
from smb_handler import run as smb_run
# from csv_handler import CSVHandler
from csv_validator import CSVValidator
from db import update_data
# from convert_charset import convert_encoding
from server_status import AsyncKeyValueStore
# import inspect

setup_logger()
logger = logging.getLogger(__name__)


async def ln(num: int = 30) -> str:
    """Возвращает строку из символов '='."""
    return f'\n{"=" * num}'


async def perform_smb_task(srv_status, shop_id: str) -> None:
    """Выполняет задачу получения файла по SMB и его обработки."""
    start_connect_time = time()
    env = get_smb_config()
    debug_mode = env['debug_mode']
    hostname = env['host_template'].format(shop_id)
    # Формирование полного пути к файлу для сохранения
    # download_path = os_join(env['to_path'], shop_id + Path(env['file_pattern']).suffix)
    file_path = None

    smb_config = {
        'server': hostname,
        'username': env['user'],
        'password': env['password'],
        'share': env['share'],
        'remote_path': env['smb_path'],
        'file_pattern': env['file_pattern'],
        'download_path': env['to_path'],
        'download_file_name': shop_id + Path(env['file_pattern']).suffix,
        # 'download_file_name': shop_id,
        # 'multiple': env['multiple']
    }

    try:
        file_path = await smb_run(smb_config)

        logger.debug(f'Время подключения к "{hostname}": {time() - start_connect_time:.2f} секунд.')

        if file_path:
            # convert_encoding перенесен в класс CSVHandler
            # try:
            #     await convert_encoding(file_path)  # Конвертируем файл в UTF-8, если необходимо
            # except Exception as e:
            #     logger.error(f'Ошибка при конвертации файла магазина {shop_id} в UTF-8: {e}')

            try:
                # handler = CSVHandler()
                handler = CSVValidator()
                valid_records = await handler.process_csv(file_path)

                # await run_csv_reader(file_path)
            except Exception as e:
                if not debug_mode:
                    # Получаем текущее имя функции и номер строки
                    # current_frame = inspect.currentframe()
                    # Получаем исходный код текущей и предыдущей инструкций
                    # try:
                    #     function_name = inspect.getframeinfo(current_frame.f_back).function
                    #     line_number = inspect.getframeinfo(current_frame.f_back).lineno
                    # finally:
                    #     # Удаляем ссылку на фрейм, чтобы избежать утечек памяти
                    #     del current_frame
                    # logger.error(
                    #     f'Ошибка в функции {function_name} на строке {line_number} при чтении файла {shop_id} в UTF-8: {e}')
                    logger.error(f'Ошибка при чтении файла магазина {shop_id} в UTF-8: {e}')
                else:
                    raise
                
            try:
                # print(f'type: {type(valid_records)}')
                if valid_records:
                    logger.info('Validation successful.')
                    # импортируем данные в БД
                    # pprint([shop_id, valid_records])
                    await update_data(shop_id, valid_records)
                
                else:
                    logger.warning('Failed to process records.')
            except Exception as e:
                if not debug_mode:
                    # current_frame = inspect.currentframe()
                    # try:
                    #     function_name = inspect.getframeinfo(current_frame.f_back).function
                    #     line_number = inspect.getframeinfo(current_frame.f_back).lineno
                    # finally:
                    #     del current_frame
                    # logger.error(
                    #     f'Ошибка в функции {function_name} на строке {line_number} при импорте данных в БД {shop_id}: {e}')
                    logger.error(f'Ошибка при импорте данных в БД для магазина {shop_id}: {e}')
                else:
                    raise
                
    except IndexError as e:
        logger.error(f'Индекс вышел за пределы диапазона при обработке магазина {shop_id}: {e}')
    except Exception as e:
        if not debug_mode:
            logger.error(f'Ошибка при обработке магазина {shop_id}: {e}')
        else:
            raise
    finally:
        # Обновление статуса сервера
        # await update_server_status(hostname, bool(file_path))
        await srv_status.set_value(hostname, bool(file_path))

        logger.info(f'Обновление статуса сервера: "{hostname}"')


async def run():
    """Основная функция для запуска цикла обработки."""
    now = dt.now()
    formatted_date_time = now.strftime('on %Y.%m.%d at %H:%M')

    logger.info(f'Скрипт запущен в {formatted_date_time}.')

    srv_status = AsyncKeyValueStore()

    env = get_schedule_config()
    hosts = get_smb_config()['hosts']

    while True:
        start_cycle_time = time()

        tasks = [aio_create_task(perform_smb_task(srv_status, shop_id)) for shop_id in hosts]
        # Ждем завершения всех задач
        await aio_gather(*tasks)

        await srv_status.save_to_file()

        logger.info(f'Время выполнения цикла: {time() - start_cycle_time:.2f} секунд.')
        logger.info(f'Пауза на: {env["check_interval"]} секунд.')
        await aio_sleep(env['check_interval'])


if __name__ == '__main__':
    try:
        aio_run(run())
    except KeyboardInterrupt:
        logger.warning(f'Программа была остановлена пользователем.')