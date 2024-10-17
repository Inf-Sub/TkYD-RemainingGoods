__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/02'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.2.2'

from pathlib import Path
import re
import aiofiles
import asyncio

from app.utils.logging_config import logging, setup_logging


setup_logging()
logger = logging.getLogger(__name__)


async def run(log_file: str, pattern: str):
    # await convert_to_utf8(log_file)

    # Открываем файл в режиме чтения
    async with aiofiles.open(log_file, 'r', encoding='utf-8') as file:
        # Читаем все строки из файла
        lines = await file.readlines()

    # Регулярное выражение для поиска слова 'заказ', обрамленного пробелами
    pattern = re.compile(pattern)  # r'\b заказ \b'
    # print(f"pattern: {pattern == r'\b заказ \b'}")
    # print(f"pattern var: {type(pattern)} & pattern text: {type(r'\b заказ \b')}")
    # print(f"pattern var: {pattern} & pattern text: {r'\b заказ \b'}")

    # Проходим по строкам и выводим те, которые соответствуют шаблону
    matching_lines = [line for line in lines if pattern.search(line)]

    # For Test: Выводим результаты
    for line in matching_lines:
        # print(line.strip())

        # Разбиваем строку на части
        parts = line.strip().split()
        timestamp = f'{parts[0]} {parts[1]}'
        status = parts[2]
        order = parts[4].split('_')
        order_number = order[0]
        creator_id = order[1].split('.')[0]
        user_login = parts[5]
        print(
            f'| Shop: {Path(log_file).stem}\t| timestamp: {timestamp}\t'
            f'| status: {status}{"\t" if status == "Новый" else ""}\t'
            f'| order_number: {order_number}\t| creator_id: {creator_id}\t'
            f'| user_login: {user_login}\t|'
        )


if __name__ == '__main__':
    async def test_run():
        # from os.path import join
        from os import getenv
        from dotenv import load_dotenv

        # from app.config import LOCAL_REPO_DIR as LOCAL_REPO_DIR

        # Загрузка переменных из .env файла
        load_dotenv()

        shops = getenv('SHOPS').replace(' ', '').split(',')
        # LOG_SMP_PATH = join(LOCAL_REPO_DIR, getenv('LOG_SMP_PATH'))
        pattern = getenv('LOG_FIND_PATTERN')

        tasks = []
        for shop_id in shops:
            shop_log_file = '{}.log'.format(shop_id)
            if Path(shop_log_file).exists():
                print(f'File: "{shop_log_file}" - exist. Read file...')
                tasks.append(run(shop_log_file, pattern))
            else:
                print(f'File: "{shop_log_file}" - does not exist')

        await asyncio.gather(*tasks)

    asyncio.run(test_run())
