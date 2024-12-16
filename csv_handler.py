__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.6.6'

from os.path import join as os_join
from csv import DictReader as csv_DictReader
from aiofiles import open as aio_open
from chardet import detect as char_detect
from typing import List, Dict, Any, Optional
from pathlib import Path
from re import findall as re_findall, sub as re_sub, search as re_search, compile as re_compile, IGNORECASE
from config import get_csv_config

from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


class CSVHandler:
    def __init__(self):
        self.data_name = None
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

    # version 2.5.5
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def is_valid_ean13(barcode_ean13: str) -> bool:
            if len(barcode_ean13) != 13 or not barcode_ean13.isdigit():
                return False
            sum_even = sum(int(barcode_ean13[i]) for i in range(1, 12, 2))
            sum_odd = sum(int(barcode_ean13[i]) for i in range(0, 12, 2))
            checksum = (10 - (sum_odd + 3 * sum_even) % 10) % 10
            return checksum == int(barcode_ean13[-1])
        
        
        def get_valid_number(value, max_value, pattern):
            if isinstance(value, (int, float)) and 0 < value <= max_value:
                return float(value)
            elif isinstance(value, str) and value:
                found_value = re_search(pattern, value)
                if found_value:
                    number = float(found_value.group().replace(',', '.'))
                    if 0 < number <= max_value:
                        return number
            return None


        # def extract_number_from_string(value: Optional[str]) -> Optional[float]:
        #     if value is None:
        #         return None
        #
        #     matches = re_findall(r'\d+\.?\d*', value)  # Используем re.findall вместо re_findall
        #     if matches:
        #         # print(f'matches {matches[0]}')
        #         return float(matches[0])  # Преобразование первого найденного числа в float
        #     return None
        
        
        def parse_composition(composition_str: str, replacements: Dict[str, str]) -> Optional[float]:
            
            # Преобразование строки к нижнему регистру для унификации
            composition_str = composition_str.lower()
            
            # Замена сокращений на полные названия
            for short_name, full_name in replacements.items():
                composition_str = composition_str.replace(short_name.lower(), full_name.lower())
            
            # Регулярное выражение для поиска составов в формате "XX% материал" или "материал XX%"
            pattern = r'(\d+(?:[\.,]\d+)?)\s*%?\s*([а-яёa-z]+)|([а-яёa-z]+)\s*(\d+(?:[\.,]\d+)?)\s*%?'
            
            # Создание словаря для результата
            composition_dict = {}
            
            # Поиск всех совпадений
            matches = re_findall(pattern, composition_str)
            
            # Обработка всех найденных элементов
            for match in matches:
                # Определение правильного порядка числа и названия
                if match[0]:  # Формат "XX% материал"
                    percentage, material = match[0], match[1]
                else:  # Формат "материал XX%"
                    percentage, material = match[3], match[2]
                
                # Приведение имени материала к стандартному виду
                material = material.capitalize()
                
                # Заменяем запятые на точки в числах
                percentage = percentage.replace(',', '.')
                
                # Запись в словарь
                composition_dict[material] = float(percentage)
            
            return composition_dict

        valid_data = []
        
        key_barcode = 'Packing.Barcode'
        key_article = 'Артикул'
        key_unit_name = 'Packing.Name'
        key_quantity = 'Packing.Колво'
        key_stock = 'Packing.СвободныйОстаток'
        key_storage_location = 'Packing.МестоХранения'
        key_width = 'Packing.Ширина'
        key_density = 'Packing.Плотность'
        key_compound = 'Packing.Состав'
        key_price = 'Packing.Цена'
        key_new_price = 'Packing.НоваяЦена'
        key_discount = 'Packing.Скидка'
        key_promo_period = 'Packing.СрокАкции'
        key_organization = 'Packing.Организация'
        key_product_name = 'Наименование'
        key_code = 'Код'
        key_description = 'Description'
        key_additional_description = 'AdditionalDescription'
        key_factory = 'Packing.Производитель'
        key_factory_country = 'Packing.СтранаПроизводства'
        key_factory_address = 'Packing.АдресПроизводителя'

        pattern_float = re_compile(r'\d+(?:[\.,]\d+)?')
        dict_replacements = {
            'П/Э': 'Полиэстер', 'П/А': 'Полиамид', 'Металлизированная нить': 'Люрекс', 'альпаки': 'альпака', }

        try:
            for row in data:
                if key_barcode in row and isinstance(row[key_barcode], str):
                    barcode = row[key_barcode]

                    # Проверка поля 'Packing.Barcode' на валидность значения, также информативная проверка
                    # на корректность EAN-13
                    if len(barcode) == 13 and barcode.isdigit():
                        if self.env['invalid_ean13'] and not is_valid_ean13(barcode):
                            logger.info(f'Invalid EAN-13 barcode: "{barcode}". This is "CODE-128".')
                        
                        
                        # Проверка поля 'Packing.Колво' на наличие числа (не пусто)
                        free_quantity = row.get(key_quantity)
                        try:
                            row[key_quantity] = float(free_quantity)
                        except (ValueError, TypeError):
                            logger.warning(
                                f'Shop: {self.data_name}. '
                                f'Invalid or None value: "{free_quantity}" in "{key_quantity}": {row}')
                            continue  # Пропускаем этот ряд (row), так как значение не является числом или отсутствует
                        
                        
                        # Проверка поля 'Packing.СвободныйОстаток' на наличие числа (не пусто)
                        free_stock = row.get(key_stock)
                        try:
                            row[key_stock] = float(free_stock)
                        except (ValueError, TypeError):
                            logger.warning(
                                f'Shop: {self.data_name}. '
                                f'Invalid or None value: "{free_stock}" in "{key_stock}": {row}')
                            # continue  # Пропускаем этот ряд, так как значение не является числом или отсутствует
                        
                        
                        # Проверка поля 'Packing.Ширина' и получение из него цифрового значения <= self.env['max_width']
                        width_value = get_valid_number(row.get(key_width, ''), self.env['max_width'], pattern_float)
                        if width_value is None:
                            width_value = get_valid_number(
                                row.get(key_description, ''), self.env['max_width'], pattern_float)
                        row[key_width] = width_value
                        
                        
                        # Проверка поля 'Packing.АдресПроизводителя' и удаление подстроки 'адрес:'
                        factory_address_value = re_sub(r'\s+', ' ', row.get(
                            key_factory_address, '').replace('адрес:', '').strip())
                        row[key_factory_address] = factory_address_value if factory_address_value else None
                        
                        
                        # Проверка поля 'Packing.МестоХранения'
                        storage_location_value = re_sub(r'\s+', ' ', row.get(key_storage_location, '').strip())
                        row[key_storage_location] = [
                            value.strip() for value in storage_location_value.split(',')
                        ] if storage_location_value else None
                        
                        
                        # Проверка поля 'Packing.Name'
                        units_value = re_sub(r'\s+', ' ', row.get(key_unit_name, '').replace('.', '').strip())
                        # row[key_unit_name] = units_value if units_value else None
                        # Костыль:
                        # если `units_value` не равно `None`, не равно `'м'` и не равно `'шт'`, то
                        # `row[key_unit_name]` получит значение `'к-т'` (косплект). В противном случае
                        # `row[key_unit_name]` примет значение `units_value`.
                        row[key_unit_name] = 'к-т' if (
                                units_value is not None and units_value != 'м' and units_value != 'шт') else units_value
                        
                        
                        # Проверка поля 'Packing.Состав'
                        compound_value = re_sub(r'\s+', ' ', row.get(key_compound, '').strip())
                        if compound_value:
                            row[key_compound] = parse_composition(compound_value, dict_replacements)
                            sum_compound_value = sum(row[key_compound].values())
                            if sum_compound_value != 100:
                                logger.warning(
                                    f'Shop: {self.data_name}. Compound: Barcode: {barcode}. Sum: {sum_compound_value}. '
                                    f'Original: {compound_value}. After parse: {row[key_compound]}')
                                row[key_compound] = None
                        else:
                            row[key_compound] = None
                            
                        # temp del (not use)
                        # del row[key_product_name]  # ?
                        
                        del row[key_factory]
                        del row[key_factory_country]
                        del row[key_factory_address]
                        
                        del row[key_new_price]
                        del row[key_promo_period]
                        del row[key_discount]
                        del row[key_organization]

                        # unnecessary variables
                        del row[key_code]
                        del row[key_description]
                        del row[key_additional_description]
                        
                        valid_data.append(row)
                    else:
                        logger.warning(f'Invalid barcode: "{barcode}": {row}')
                else:
                    logger.warning(f'Missing or invalid barcode key in data: {row}')
        except Exception as e:
            logger.error(f'Shop: {self.data_name}. Error validating data: {e}')
            raise

        # print(f'Valid_data: {valid_data}')
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
            self.data_name = input_path.name
            
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
    from random import randrange

    smb_config = get_smb_config()

    handler = CSVHandler()
    csv_file_path = os_join(smb_config['to_path'], 'OMS-01.csv')  # Замените на ваш путь
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
