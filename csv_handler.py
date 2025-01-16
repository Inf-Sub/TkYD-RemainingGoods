__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/19'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.7.6'

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
        self.data_name = None

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
            logger.error(f'Unable to determine encoding of file {input_file.name}. Encoding is None')
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

    async def process_csv(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            input_path = Path(file_path)
            self.data_name = input_path.stem
            
            await self.convert_encoding(input_path)
            data = self.read_csv(input_path, delimiter=self.env['csv_delimiter'])
            # valid_data = self.validate_data(data)
            # return valid_data
            return data
        except Exception as e:
            logger.error(f'Error processing CSV file {file_path}: {e}')
            return []
        
        
if __name__ == '__main__':
    from asyncio import run as async_run
    from config import get_smb_config
    from random import randrange

    smb_config = get_smb_config()

    handler = CSVHandler()
    csv_file_path = os_join(smb_config['to_path'], 'TST.csv')  # Замените на ваш путь
    print(f'Read file: {csv_file_path}')
    valid_records = async_run(handler.process_csv(csv_file_path))

    if valid_records:
        max_num = len(valid_records)
        print(f'Валидация прошла успешно, обработано записей: {max_num}')
        for num in range(max_num):
            if valid_records[num]['Packing.Barcode'] == '2103203216754':
                print(f'{valid_records[num]}')
                break
        # while True:
        #     num = randrange(0, max_num)
        #     print(f'{num} < {max_num}')
        #     place = valid_records[num]['Packing.МестоХранения']
        #     compound = valid_records[num]['Packing.Состав']
        #
        #     if (place is not None and len(place) > 1) or (compound is not None and len(compound) > 1):
        #         print(f'Ширина: {valid_records[num]['Packing.Ширина']}')
        #         print(f'МестоХранения: {place}')
        #         print(f'МестоХранения: {compound}')
        #         print(f'Запись #{num}:')
        #         print(f'{valid_records[num]}')
        #         # for record in valid_records:
        #         #     print(record)
        #         break
    else:
        print('Не удалось обработать записи.')
    