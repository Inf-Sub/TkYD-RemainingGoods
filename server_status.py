__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/22'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.8.1'


from typing import Union, Dict, Any
from aiofiles import open as aio_open

from config import get_status_config
from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


class AsyncKeyValueStore:
    def __init__(self) -> None:
        self.store: Dict[str, bool] = {}
        self.env: Dict[str, Any] = get_status_config()

    async def set_value(self, key: str, value: Union[str, bool, None]) -> None:
        """
        Устанавливает значение для ключа в асинхронном режиме. Обновляет значение, если ключ существует, добавляет новый иначе.
        
        Args:
            key (str): Ключ для хранения.
            value (Union[str, bool, None]): Значение. Не пустая строка -> True, Иначе -> False.
        
        Returns:
            None
        """
        if value is None:
            value = False

        if key in self.store:
            logger.info(f'Updating value for key: {key} to {value}')
        else:
            logger.info(f'Adding new key: {key} with value: {value}')

        self.store[key] = value

    async def get_store(self) -> Dict[str, bool]:
        """
        Асинхронно возвращает текущее состояние хранилища в виде словаря.

        Returns:
            (Dict[str, bool]): Словарь текущих состояний хранилища.
        """
        logger.info('Returning current store')
        return self.store
    
    async def save_to_file(self) -> None:
        """
        Асинхронно сохраняет текущее состояние хранилища в файл, путь к которому
        указывается в конфигурации окружения. Если путь не установлен, записывается ошибка в лог.
        
        Returns:
            None
        """
        file_path = self.env.get('path')
        if not file_path:
            logger.error('"STATUS_FILE_PATH" is not set in .env file')
            return
        
        logger.info(f'Saving store to file: {file_path}')
        
        try:
            async with aio_open(file_path, 'w') as f:
                for key, value in self.store.items():
                    await f.write(f'{key}: {"Available" if value else "Unavailable"}\n')
            logger.info(f'Successfully saved store to {file_path}')
        except Exception as e:
            logger.error(f'Failed to save store to {file_path}: {str(e)}')
   

async def main_test():
    """
    Пример асинхронного использования класса AsyncKeyValueStore.
    Создает экземпляр хранилища, добавляет и обновляет значения, получает текущее состояние и сохраняет его в файл.
    
    Returns:
        None
    """
    kv_store = AsyncKeyValueStore()
    await kv_store.set_value('key1', 'value1')
    await kv_store.set_value('key2', 'value2')
    await kv_store.set_value('key1', 'updated_value1')

    current_store = await kv_store.get_store()
    print('Current Store:', current_store)

    await kv_store.save_to_file()


if __name__ == '__main__':
    from asyncio import run as aio_run
    aio_run(main_test())
