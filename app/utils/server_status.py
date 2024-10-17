__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/14'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.2.8'


import aiofiles
from os import getenv
from os.path import exists
from dotenv import load_dotenv


load_dotenv()

STATUS_FILE_PATH = getenv('STATUS_FILE_PATH')


async def update_server_status(hostname: str, log_file_path: bool) -> None:
    # Проверка существования файла и его создание, если он отсутствует
    if not exists(STATUS_FILE_PATH):
        # Создание пустого файла
        async with aiofiles.open(STATUS_FILE_PATH, mode='w') as file:
            await file.write('')

    status_line = f"{hostname} - {'Available' if log_file_path else 'Unavailable'}\n"
    updated = False

    # Чтение текущих статусов
    async with aiofiles.open(STATUS_FILE_PATH, mode='r') as file:
        lines = await file.readlines()

    # Обновление или добавление статуса
    async with aiofiles.open(STATUS_FILE_PATH, mode='w') as file:
        for line in lines:
            if line.startswith(hostname):
                await file.write(status_line)
                updated = True
            else:
                await file.write(line)

        if not updated:
            await file.write(status_line)
