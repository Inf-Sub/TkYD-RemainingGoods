__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/27'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.5.3'

from os.path import join as os_join
from csv import DictReader as csv_DictReader
from aiofiles import open as aio_open
from chardet import detect as char_detect
from typing import List, Dict, Any, Optional
from pathlib import Path
from re import findall as re_findall, sub as re_sub
from config import get_csv_config

from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


class CSVHandler:
    def __init__(self):
        self.env = get_csv_config()

    @staticmethod
    async def detect_encoding(file_path: Path, sample_size: int = 1024) -> Optional[str]:
        # try:
        async with aio_open(file_path, 'rb') as file:
            raw_data = await file.read(sample_size)
            result = char_detect(raw_data)
            encoding = result['encoding']
            return encoding.lower() if encoding else None
        # except Exception as e:
        #     logger.error(f'Unable to determine encoding of file {file_path.name}: {e}.')
        #     return None

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

    # version 2.5.4
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def is_valid_ean13(barcode_ean13: str) -> bool:
            if len(barcode_ean13) != 13 or not barcode_ean13.isdigit():
                return False
            sum_even = sum(int(barcode_ean13[i]) for i in range(1, 12, 2))
            sum_odd = sum(int(barcode_ean13[i]) for i in range(0, 12, 2))
            checksum = (10 - (sum_odd + 3 * sum_even) % 10) % 10
            return checksum == int(barcode_ean13[-1])

        def extract_number_from_string(value: str) -> Optional[float]:
            matches = re_findall(r'\d+\.?\d*', value)  # Поиск чисел в строке
            if matches:
                return float(matches[0])  # Преобразование первого найденного числа в float
            return None

        valid_data = []

        try:
            for row in data:
                check_key_barcode = 'Packing.Barcode'
                check_key_stock = 'Packing.СвободныйОстаток'
                check_key_width = 'Packing.Ширина'
                check_key_factory_address = 'Packing.АдресПроизводителя'
                max_width = 200  # 200 mm

                if check_key_barcode in row and isinstance(row[check_key_barcode], str):
                    barcode = row[check_key_barcode]

                    # Проверка поля 'Packing.Barcode' на валидность значения, также информативная проверка
                    # на корректность EAN-13
                    if len(barcode) == 13 and barcode.isdigit():
                        if self.env['invalid_ean13'] and not is_valid_ean13(barcode):
                            logger.info(f'Invalid EAN-13 barcode: "{barcode}". This is "CODE-128".')

                        # Проверка поля 'Packing.СвободныйОстаток' на наличие числа (не пусто) и не равно NoneType
                        free_stock = row.get(check_key_stock)

                        # TODO: Проверить корректную работу continue - скорее всего тут нужна перезапись на пустое
                        #  значение
                        if free_stock is not None:
                            try:
                                float(free_stock)
                            except ValueError:
                                logger.warning(f'Invalid numeric value: "{free_stock}" in "{check_key_stock}": {row}')
                                continue  # Пропускаем этот ряд, так как значение не является числом
                        else:
                            logger.warning(f'None value found in "{check_key_stock}": {row}')
                            continue  # Пропускаем этот ряд, так как значение отсутствует

                        # Проверка поля 'Packing.Ширина' и получение из него цифрового значения <= max_width
                        width_value = row.get(check_key_width, '')
                        extracted_number = extract_number_from_string(width_value)
                        if extracted_number is not None and extracted_number <= max_width:
                            row[check_key_width] = extracted_number
                        else:
                            row[check_key_width] = ''  # Устанавливаем пустое значение, если число не найдено

                        # Проверка поля 'Packing.АдресПроизводителя' и удаление подстроки 'адрес:'
                        factory_address_value = row.get(check_key_factory_address, '')
                        if factory_address_value is not None:
                            factory_address_value = factory_address_value.replace('адрес:', '')
                            factory_address_value = re_sub(r'\s+', ' ', factory_address_value).strip()
                            row[check_key_factory_address] = factory_address_value
                        else:
                            row[check_key_factory_address] = ''  # Устанавливаем пустое значение, если значение == None

                        valid_data.append(row)
                    else:
                        logger.warning(f'Invalid barcode: "{barcode}": {row}')
                else:
                    logger.warning(f'Missing or invalid barcode key in data: {row}')
        except Exception as e:
            logger.error(f'Error validating data: {e}')
            raise

        return valid_data

    # # version 2.5.1
    # @staticmethod
    # def validate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     def is_valid_ean13(barcode: str) -> bool:
    #         if len(barcode) != 13 or not barcode.isdigit():
    #             return False
    #         # Проверка контрольной суммы для формата EAN-13
    #         sum_even = sum(int(barcode[i]) for i in range(1, 12, 2))
    #         sum_odd = sum(int(barcode[i]) for i in range(0, 12, 2))
    #         checksum = (10 - (sum_odd + 3 * sum_even) % 10) % 10
    #         return checksum == int(barcode[-1])
    #
    #     valid_data = []
    #     try:
    #         for row in data:
    #             check_key = 'Packing.Barcode'
    #             if check_key in row and isinstance(row[check_key], str):
    #                 barcode = row[check_key]
    #                 if len(barcode) == 13 and barcode.isdigit():
    #                     if not is_valid_ean13(barcode):
    #                         logger.info(f'Barcode "{barcode}" is not a valid EAN-13 format: {row}')
    #
    #                     check_key = 'Packing.СвободныйОстаток'
    #                     free_stock = row.get(check_key)
    #                     if free_stock is not None:
    #                         try:
    #                             # Преобразуем к float и проверяем успешность преобразования
    #                             float(free_stock)
    #                             valid_data.append(row)
    #                         except ValueError:
    #                             logger.warning(f'Invalid numeric value: "{free_stock}" in "{check_key}": {row}')
    #                     else:
    #                         logger.warning(f'None value found in "{check_key}": {row}')
    #                 else:
    #                     logger.warning(f'Invalid barcode length or non-digit characters: "{barcode}": {row}')
    #             else:
    #                 logger.warning(f'Invalid data: {row}')
    #     except Exception as e:
    #         logger.error(f'Error validating data: {e}')
    #         raise
    #     return valid_data

    # # version 2.5.0
    # @staticmethod
    # def validate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    #     valid_data = []
    #     try:
    #         for row in data:
    #             check_key = 'Packing.Barcode'
    #             if check_key in row and isinstance(row[check_key], str):
    #                 check_key = 'Packing.СвободныйОстаток'
    #                 free_stock = row.get(check_key)
    #                 if free_stock is not None:
    #                     try:
    #                         # Преобразуем к float и проверяем успешность преобразования
    #                         float(free_stock)
    #                         valid_data.append(row)
    #                     except ValueError:
    #                         logger.warning(f'Invalid numeric value: "{free_stock}" in "{check_key}": {row}')
    #                 else:
    #                     logger.warning(f'None value found in "{check_key}": {row}')
    #             else:
    #                 logger.warning(f'Invalid data: {row}')
    #     except Exception as e:
    #         logger.error(f'Error validating data: {e}')
    #         raise
    #     return valid_data

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
    from random import randint

    smb_config = get_smb_config()

    handler = CSVHandler()
    csv_file_path = os_join(smb_config['to_path'], 'TOM-01.csv')  # Замените на ваш путь
    valid_records = async_run(handler.process_csv(csv_file_path))

    if valid_records:
        max_num = len(valid_records)
        print(f'Валидация прошла успешно, обработано записей: {max_num}')
        num = randint(0, max_num)
        print(f'Запись #{num}:')
        print(f'{valid_records[num]}')
        # for record in valid_records:
        #     print(record)
    else:
        print('Не удалось обработать записи.')
