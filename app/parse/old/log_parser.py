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
from pprint import pprint

from logger import logging, setup_logging


setup_logging()
logger = logging.getLogger(__name__)


async def parse_log(log_file: str, pattern: str) -> None:
    try:
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

        # Список для хранения данных в виде словарей
        # data = []

        # For Test: Выводим результаты
        for line in matching_lines:
            # print(line.strip())

            # Разбиваем строку на части
            parts = line.strip().split()
            # print(parts)
            timestamp = f'{parts[0]} {parts[1]}'
            status = parts[2]
            order = parts[4].split('_')
            order_number = order[0]
            creator_id = order[1].split('.')[0]
            user_login = parts[5]

            # # Создаем словарь для текущей строки
            # entry = {
            #     "Shop": Path(log_file).stem,
            #     "timestamp": timestamp,
            #     "status": status,
            #     "order_number": order_number,
            #     "creator_id": creator_id,
            #     "user_login": user_login
            # }
            # # Добавляем словарь в список
            # data.append(entry)
            #
            # # Преобразуем список словарей в JSON
            # json_data = json.dumps(data, ensure_ascii=False, indent=4)
            #
            # print(json_data)

            pprint(
                f'| Shop: {Path(log_file).stem}\t| timestamp: {timestamp}\t'
                f'| status: {status}{"\t" if status == "Новый" else ""}\t'
                f'| order_number: {order_number}\t| creator_id: {creator_id}\t'
                f'| user_login: {user_login}\t|'
            )
    except Exception as e:
        logger.error(f'Ошибка при обработке файла {log_file}: {e}')


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
                # print(f'File: "{shop_log_file}" - exist. Read file...')
                logging.info(f'File: "{shop_log_file}" - exist. Read file...')
                tasks.append(parse_log(shop_log_file, pattern))
            else:
                # print(f'File: "{shop_log_file}" - does not exist')
                logging.warning(f'File: "{shop_log_file}" - does not exist')

        await asyncio.gather(*tasks)

    asyncio.run(test_run())
