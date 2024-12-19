__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.7.4'

from typing import Dict


def get_csv_keys() -> Dict[str, str]:
    return {'barcode': 'Packing.Barcode', 'article': 'Артикул', 'unit_name': 'Packing.Name',
            'quantity': 'Packing.Колво', 'stock': 'Packing.СвободныйОстаток',
            'storage_location': 'Packing.МестоХранения', 'width': 'Packing.Ширина', 'density': 'Packing.Плотность',
            'compound': 'Packing.Состав', 'price': 'Packing.Цена', 'new_price': 'Packing.НоваяЦена',
            'discount': 'Packing.Скидка', 'promo_period': 'Packing.СрокАкции', 'organization': 'Packing.Организация',
            'product_name': 'Наименование', 'description': 'Description',
            'additional_description': 'AdditionalDescription', 'factory': 'Packing.Производитель', 'code': 'Код',
            'factory_country': 'Packing.СтранаПроизводства', 'factory_address': 'Packing.АдресПроизводителя'}
