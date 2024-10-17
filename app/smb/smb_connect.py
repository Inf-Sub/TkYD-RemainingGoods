__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/09/29'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.0.0'


from os import getenv
from os.path import join, splitext
from pathlib import Path
from time import sleep, time
from ping3 import ping
from smb.SMBConnection import SMBConnection
from dotenv import load_dotenv
from fnmatch import fnmatch
# import logging
from app.utils.logging_config import logging, setup_logging  # импортируем наш модуль с настройками логгера
from app.config import REPO_DIR as LOCAL_REPO_DIR


setup_logging()
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования


# Загрузка переменных из .env файла
load_dotenv()

SHOPS = getenv('SHOPS').replace(' ', '').split(',')
SMB_HOSTNAME_TEMPLATE = getenv('SMB_HOSTNAME_TEMPLATE')
SMB_PORT = int(getenv('SMB_PORT'))
SMB_TIMEOUT = int(getenv('SMB_TIMEOUT'))
SMB_SHARE = getenv('SMB_SHARE')
SMB_USERNAME = getenv('SMB_USERNAME')
SMB_PASSWORD = getenv('SMB_PASSWORD')
LOG_SMP_PATH = join(REPO_DIR, getenv('LOG_SMP_PATH')) + '-sync'
LOG_FILE_PATTERN = getenv('LOG_FILE_PATTERN')
SMB_SLEEP_INTERVAL = int(getenv('SMB_SLEEP_INTERVAL'))


def check_host_availability(hostname: str) -> bool:
    response = ping(hostname)
    return bool(response)


def download_files_from_share(
        hostname: str, share: str, username: str, password: str, download_log_path: str,
        shop_name: str, file_pattern: str
) -> None:
    try:
        conn = SMBConnection(username, password, 'localmachine', hostname, use_ntlm_v2=True, is_direct_tcp=True)
        # print(f'conn = SMBConnection(username={username}, password={password}, hostname={hostname})')
        conn.connect(ip=hostname, port=SMB_PORT, timeout=SMB_TIMEOUT)
        # print(f'conn.connect(ip={hostname}, port={SMB_PORT}, timeout={SMB_TIMEOUT})')
        shared_files = conn.listPath(share, '/')
        logger.info(f'shared_files:\t{[file.filename for file in shared_files]}')

        matching_files = [f for f in shared_files if fnmatch(f.filename, file_pattern)]

        if not matching_files:
            logger.info(f'No files matching pattern {file_pattern} found on {hostname}.')
            return

        # Проверить существование директории
        path = Path(download_log_path)
        # if not os.path.exists(download_log_path):
        if not path.exists():
            # Создать директорию
            path.mkdir(parents=True, exist_ok=True)
            # os.makedirs(download_log_path)
            logger.info(f'Directory "{download_log_path}" created.')
        # else:
        #     print(f"Directory {download_log_path} already exists.")

        for file in matching_files:
            logger.info(f'filename: "{file.filename}" => "{shop_name}{splitext(file.filename)[1]}"')
            file_path = join(download_log_path, f'{shop_name}{splitext(file.filename)[1]}')
            print(f'file_path: {file_path}')
            with open(file_path, 'wb') as local_file:
                conn.retrieveFile(share, file.filename, local_file)
                logger.info(f'Downloaded "{file.filename}" from "{hostname}" to "{download_log_path}".')

        conn.close()
    except Exception as e:
        logger.info(f'Ошибка при работе с сетевой шарой {hostname}:\t{e}')


def smb_connection_timer() -> None:
    i = 0
    while True:
        start_time = time()

        for shop_name in SHOPS:
            hostname = SMB_HOSTNAME_TEMPLATE.format(shop_name)
            # print(f'check: {check_host_availability(hostname)} hostname: {hostname}')
            if check_host_availability(hostname):
                logger.info(f'{hostname} доступен. Подключение к сетевой шаре...')
                download_files_from_share(
                    hostname=hostname, share=SMB_SHARE, username=SMB_USERNAME, password=SMB_PASSWORD,
                    download_log_path=LOG_SMP_PATH, shop_name=shop_name, file_pattern=LOG_FILE_PATTERN
                )
            else:
                logger.info(f'{hostname} недоступен.')

        end_time = time()
        i += 1
        print(f'Время выполнения цикла {i}: {end_time - start_time} секунд.')
        print(f'Пауза на: {SMB_SLEEP_INTERVAL} секунд')
        sleep(SMB_SLEEP_INTERVAL)


def run():
    smb_connection_timer()


if __name__ == '__main__':
    run()

