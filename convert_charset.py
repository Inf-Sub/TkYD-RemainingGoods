__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/14'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.4.2'

from asyncio import run as async_run
from aiofiles import open as aio_open
from chardet import detect as char_detect
# import cchardet import detect as char_detect
from typing import Optional
from pathlib import Path

from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


async def detect_encoding(file_path: Path, sample_size: int = 1024) -> Optional[str]:
    """
    Определяет кодировку файла.

    :param file_path: Путь к файлу для определения кодировки.
    :param sample_size: Количество байт для анализа. По умолчанию 1024 байта.
    :return: Кодировка файла или None в случае ошибки.
    """
    try:
        async with aio_open(file_path, 'rb') as file:
            raw_data = await file.read(sample_size)
            result = char_detect(raw_data)
            encoding = result['encoding']
            return encoding.lower() if encoding else None
    except Exception as e:
        logger.error(f'Unable to determine encoding of file {file_path.name}: {e}.')
        return None


async def convert_encoding(
        input_file: str, output_file: Optional[str] = None, output_encode: str = 'utf-8') -> None:
    """
    Конвертирует файл в указанную кодировку (по умолчанию UTF-8).

    :param input_file: Путь к входному файлу.
    :param output_file: Путь к выходному файлу. Если не указан, файл будет перезаписан.
    :param output_encode: Кодировка для выходного файла (по умолчанию 'utf-8').
    """
    input_path = Path(input_file)

    if not input_path.is_file():
        logger.error(f'File: {input_path.name} - does not exist!')
        return

    output_path = Path(output_file) if output_file else input_path

    encoding = await detect_encoding(input_path)

    if encoding is None:
        logger.error(f'Unable to determine encoding of file {input_path.name}.')
        return

    if encoding != output_encode:
        try:
            async with aio_open(input_path, 'r', encoding=encoding) as file:
                content = await file.read()
        except Exception as e:
            logger.error(f'Error reading file {input_path.name}: {e}')
            return

        try:
            async with aio_open(output_path, 'w', encoding=output_encode) as file:
                await file.write(content)
        except Exception as e:
            logger.error(f'Error writing file {output_path.name}: {e}')
            return

        logger.info(f'File "{output_path.name}" converted from {encoding} to {output_encode.upper()} and saved.')
    else:
        logger.info(f'File encoding: "{input_path.name}" - {output_encode.upper()}. No conversion required.')


if __name__ == '__main__':
    test_path_1 = r'/TFServerLogs/MSK-01.log'
    test_path_2 = r'/TFServerLogs/MSK-02.log'
    test_path_3 = r'c:\Users\InfSub\Clouds\Git\TkYD-MobileAppUsageStats\TFServerLogs\MSK-03.log'
    test_path_4 = r'c:\Users\InfSub\Clouds\Git\TkYD-MobileAppUsageStats\TFServerLogs\MSK-04.log'

    input_dos_file = test_path_1
    output_utf_file = test_path_1
    async_run(convert_encoding(input_dos_file, output_utf_file))

    input_dos_file = test_path_2
    async_run(convert_encoding(input_dos_file))

    input_dos_file = test_path_3
    output_utf_file = test_path_3
    async_run(convert_encoding(input_dos_file, output_utf_file))

    input_dos_file = test_path_4
    async_run(convert_encoding(input_dos_file))
