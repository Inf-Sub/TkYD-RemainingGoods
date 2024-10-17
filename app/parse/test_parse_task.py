from pathlib import Path
import re
import aiofiles
import asyncio
from dotenv import load_dotenv
from app.utils.logging_config import logging, setup_logging
from app.utils.convert_charset import convert_to_utf8  # Import the function

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()


async def run(log_file):
    async with aiofiles.open(log_file, 'r', encoding='utf-8') as file:
        lines = await file.readlines()

    pattern = re.compile(r'\b заказ \b')

    matching_lines = [line for line in lines if pattern.search(line)]

    for line in matching_lines:
        print(line.strip())


async def process_file(shop_log_file):
    await convert_to_utf8(shop_log_file)  # Convert file to UTF-8 if needed
    await run(shop_log_file)


async def test_main():
    SHOPS = ('BRN-01, CHL-01, EKB-01, IRK-01, IZH-01, KEM-01, KHB-01')
    SHOPS = SHOPS.replace(' ', '').split(',')
    LOG_SMP_PATH = 'TFServerLogs'

    tasks = []
    for shop_id in SHOPS:
        shop_log_file = '{}.log'.format(shop_id)
        if Path(shop_log_file).exists():
            print(f'File: "{shop_log_file}" - exist. Read file...')
            tasks.append(process_file(shop_log_file))
        else:
            print(f'File: "{shop_log_file}" - does not exist')

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(test_main())
