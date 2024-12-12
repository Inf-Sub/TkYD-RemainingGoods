__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/11'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.2.9'


# from aiofiles import open as aio_open
# from os.path import exists
from config import get_status_config
from logger import logging, setup_logger

setup_logger()
logger = logging.getLogger(__name__)


class AsyncKeyValueStore:
    def __init__(self):
        self.store = {}
        self.env = get_status_config()

    async def set_value(self, key: str, value: str):
        """
        Асинхронно устанавливает значение для указанного ключа.
        Если ключ уже существует, обновляет его значение, иначе добавляет новый ключ.

        :param key: str,  # Ключ для хранения.
        :param value: str,  # Значение, связанное с ключом.
        """
        if key in self.store:
            logger.info(f'Updating value for key: {key} to {value}')
        else:
            logger.info(f'Adding new key: {key} with value: {value}')

        self.store[key] = value

    async def get_store(self):
        """
        Асинхронно возвращает текущее состояние хранилища в виде словаря.

        :return: dict,  # Словарь текущих состояний хранилища.
        """
        logger.info('Returning current store')
        return self.store

    async def save_to_file(self):
        """
        Асинхронно сохраняет текущее состояние хранилища в файл, путь к которому
        указывается в конфигурации окружения. Если путь не установлен, записывается ошибка в лог.
        """
        file_path = self.env['path']
        if not file_path:
            logger.error('"STATUS_FILE_PATH" is not set in .env file')
            return

        logger.info(f'Saving store to file: {file_path}')
        with open(file_path, 'w') as f:
            for key, value in self.store.items():
                # f.write(f'{key}: {value}\n')
                f.write(f'{key}: {"Available" if value else "Unavailable"}\n')


# Пример использования
async def main_test():
    """
    Пример асинхронного использования класса AsyncKeyValueStore.
    Создает экземпляр хранилища, добавляет и обновляет значения, получает текущее состояние и сохраняет его в файл.
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


# from aiofiles import open as aio_open
# from os.path import exists
# from config import get_status_config
#
#
# async def update_server_status(hostname: str, is_log_available: bool) -> None:
#     env = get_status_config()
#
#     # Проверка существования файла и его создание, если он отсутствует
#     if not exists(env['path']):
#         # Создание пустого файла
#         async with aio_open(env['path'], mode='w') as file:
#             await file.write('')
#
#     status_line = f'{hostname} - {"Available" if is_log_available else "Unavailable"}\n'
#     updated = False
#     updated_lines = []
#
#     # Чтение текущих статусов
#     async with aio_open(env['path'], mode='r') as file:
#         lines = await file.readlines()
#
#     # Обновление или добавление статуса
#     for line in lines:
#         if line.startswith(hostname):
#             updated_lines.append(status_line)
#             updated = True
#         else:
#             updated_lines.append(line)
#
#     # Если статус не обновился, добавляем его в конец
#     if not updated:
#         updated_lines.append(status_line)
#
#     # Запись обновленных данных обратно в файл
#     async with aio_open(env['path'], mode='w') as file:
#         await file.writelines(updated_lines)
