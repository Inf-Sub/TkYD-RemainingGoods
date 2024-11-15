__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/16'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.5.0'

from os.path import join as os_join
from csv import DictReader as csv_DictReader
from aiofiles import open as aio_open
from chardet import detect as char_detect
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import get_csv_config

from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


class CSVHandler:
    def __init__(self):
        self.env = get_csv_config()

    @staticmethod
    async def detect_encoding(file_path: Path, sample_size: int = 1024) -> Optional[str]:
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
            self, input_file: Path, output_file: Optional[Path] = None, output_encode: str = 'utf-8') -> None:
        if not input_file.is_file():
            logger.error(f'File: {input_file.name} - does not exist!')
            return

        output_path = output_file if output_file else input_file

        encoding = await self.detect_encoding(input_file)

        if encoding is None:
            logger.error(f'Unable to determine encoding of file {input_file.name}.')
            return

        if encoding != output_encode:
            try:
                async with aio_open(input_file, 'r', encoding=encoding) as file:
                    content = await file.read()
            except Exception as e:
                logger.error(f'Error reading file {input_file.name}: {e}')
                return

            try:
                async with aio_open(output_path, 'w', encoding=output_encode) as file:
                    await file.write(content)
            except Exception as e:
                logger.error(f'Error writing file {output_path.name}: {e}')
                return

            logger.info(f'File "{output_path.name}" converted from {encoding} to {output_encode.upper()} and saved.')
        else:
            logger.info(f'File encoding: "{input_file.name}" - {output_encode.upper()}. No conversion required.')

    @staticmethod
    def read_csv(file_path: Path, delimiter: str = ',') -> List[Dict[str, Any]]:
        data = []
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv_DictReader(csvfile, delimiter=delimiter)
                for row in reader:
                    # Фильтруем ключи, оставляя только те, которые не равны None
                    filtered_row = {key: value for key, value in row.items() if key not in [None, '']}

                    # print("Filtered Row:")
                    # for key, value in filtered_row.items():
                    #     print(f'key: "{key}"\tvalue: "{value}"')

                    data.append(filtered_row)
        except FileNotFoundError:
            logger.error(f'File not found: {file_path}')
        except Exception as e:
            logger.error(f'Error reading CSV file {file_path}: {e}')
            raise
        return data

    @staticmethod
    def validate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_data = []
        try:
            for row in data:
                check_key = 'Packing.Barcode'
                if check_key in row and isinstance(row[check_key], str):
                    check_key = 'Packing.СвободныйОстаток'
                    free_stock = row.get(check_key)
                    if free_stock is not None:
                        try:
                            # Преобразуем к float и проверяем успешность преобразования
                            float(free_stock)
                            valid_data.append(row)
                        except ValueError:
                            logger.warning(f'Invalid numeric value: "{free_stock}" in "{check_key}": {row}')
                    else:
                        logger.warning(f'None value found in "{check_key}": {row}')
                else:
                    logger.warning(f'Invalid data: {row}')
        except Exception as e:
            logger.error(f'Error validating data: {e}')
            raise
        return valid_data

    async def process_csv(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            input_path = Path(file_path)
            await self.convert_encoding(input_path)
            data = self.read_csv(input_path, delimiter=self.env['csv_delimiter'])
            valid_data = self.validate_data(data)
            return valid_data
        except Exception as e:
            logger.error(f'Error processing CSV file {file_path}: {e}')
            return []


if __name__ == '__main__':
    from asyncio import run as async_run
    from config import get_smb_config

    smb_config = get_smb_config()

    handler = CSVHandler()
    csv_file_path = os_join(smb_config['to_path'], 'TOM-01.csv')  # Замените на ваш путь
    valid_records = async_run(handler.process_csv(csv_file_path))

    if valid_records:
        print('Валидация прошла успешно, обработанные записи:')
        # for record in valid_records:
        #     print(record)
    else:
        print('Не удалось обработать записи.')
