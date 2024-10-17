__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/04'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.0.3'


from os.path import join
from pathlib import Path
from datetime import datetime as dt

# Параметры Git
# Путь к локальной директории, где хранится скрипт
REPO_DIR = Path(__file__).parent.parent
# LOCAL_REPO_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# print(f'__file__: {__file__}')
# print(os.path.realpath(__file__))
# print(os.path.dirname(os.path.realpath(__file__)))
# print(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
# print(f'Path: {Path(__file__).parent.parent}')


# Наименование директории виртуального окружения
VENV_DIR_NAME = '.venv'
# Путь к директории виртуального окружения
VENV_PATH = join(REPO_DIR, VENV_DIR_NAME)

# Logs
LOG_DIR_NAME = 'logs'
LOG_FILE = dt.now().strftime('logfile_%Y%m%d.log')
LOG_DIR = join(REPO_DIR, LOG_DIR_NAME)
LOG_PATH = join(LOG_DIR, LOG_FILE)
LOG_LEVEL_CONSOLE = 'INFO'
LOG_LEVEL_FILE = 'INFO'

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
# if not os.path.exists(LOG_DIR):
#     os.makedirs(LOG_DIR)

# Initialize Data:
# Наименование директории с данными
DATA_DIR_NAME = 'data'
# Путь к директории с данными
DATA_DIR = join(REPO_DIR, DATA_DIR_NAME)

# Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


if __name__ == '__main__':
    print(
        f'LOCAL_REPO_DIR: {REPO_DIR}\nVENV_PATH: {VENV_PATH}\nLOG_FILE: {LOG_FILE}\nLOG_DIR: {LOG_DIR}\n'
        f'LOG_PATH: {LOG_PATH}\n'
    )
