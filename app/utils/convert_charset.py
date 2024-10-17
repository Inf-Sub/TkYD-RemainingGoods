__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/02'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.1.1'

from asyncio import run as async_run
import aiofiles
import chardet
from typing import Optional
from pathlib import Path

from app.utils.logging_config import logging, setup_logging  # импортируем наш модуль с настройками логгера


setup_logging()
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования


async def detect_encoding(file_path: str) -> str:
    async with aiofiles.open(file_path, 'rb') as file:
        raw_data = await file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        return encoding


async def convert_to_utf8(input_file: str, output_file: Optional[str] = None) -> None:
    if output_file is None:
        output_file = input_file

    if Path(input_file).exists():
        encoding = await detect_encoding(input_file)
        if encoding.lower() != 'utf-8':
            async with aiofiles.open(input_file, 'r', encoding=encoding.lower()) as file:
                content = await file.read()
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
                await file.write(content)
            logger.info(f'File "{Path(output_file).name}" converted from {encoding} to UTF-8 and saved.')
        else:
            logger.info(f'File "{Path(input_file).name}" encoding is {encoding}.')
    else:
        logger.error(f'File: {input_file} - does not exist!')


if __name__ == '__main__':
    test_path_1 = r'/TFServerLogs/MSK-01.log'
    test_path_2 = r'/TFServerLogs/MSK-02.log'
    test_path_3 = r'c:\Users\InfSub\Clouds\Git\TkYD-MobileAppUsageStats\TFServerLogs\MSK-03.log'
    test_path_4 = r'c:\Users\InfSub\Clouds\Git\TkYD-MobileAppUsageStats\TFServerLogs\MSK-04.log'

    input_dos_file = test_path_1
    output_utf_file = test_path_1
    async_run(convert_to_utf8(input_dos_file, output_utf_file))

    input_dos_file = test_path_2
    async_run(convert_to_utf8(input_dos_file))

    input_dos_file = test_path_3
    output_utf_file = test_path_3
    async_run(convert_to_utf8(input_dos_file, output_utf_file))

    input_dos_file = test_path_4
    async_run(convert_to_utf8(input_dos_file))


