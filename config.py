__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/18'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.7.5'

from os import getenv
from os.path import join
# from decouple import config
from dotenv import load_dotenv
from datetime import datetime as dt

# Загрузка переменных окружения из файла .env
load_dotenv()


def load_env() -> dict:
    """
    Загрузка переменных окружения из файла .env.
    """
    # Загрузка всех переменных, которые могут понадобиться в проекте
    return {
        'DB_HOST': getenv('DB_HOST'),
        'DB_PORT': int(getenv('DB_PORT', 3306)),
        'DB_USER': getenv('DB_USER'),
        'DB_PASSWORD': getenv('DB_PASSWORD'),
        'DB_NAME': getenv('DB_NAME'),
        'DB_SCHEMAS_PATH': getenv('DB_SCHEMAS_PATH'),
        'DB_FILE_INIT_SCHEMA': getenv('DB_FILE_INIT_SCHEMA'),
        'DB_FILE_TABLE_PREFIX': getenv('DB_FILE_TABLE_PREFIX'),
        'DB_FILE_INIT_DATA_PREFIX': getenv('DB_FILE_INIT_DATA_PREFIX'),


        'SMB_HOSTS': getenv('SHOPS'),
        'SMB_PORT': int(getenv('SMB_PORT', 445)),
        'SMB_TIMEOUT': int(getenv('SMB_TIMEOUT', 60)),
        'SMB_USER': getenv('SMB_USER'),
        'SMB_PASSWORD': getenv('SMB_PASSWORD'),
        'SMB_HOSTNAME_TEMPLATE': getenv('SMB_HOSTNAME_TEMPLATE'),
        'SMB_SHARE': getenv('SMB_SHARE'),
        'SMB_PATH': getenv('SMB_PATH'),
        'SMB_MULTIPLE': bool(getenv('SMB_MULTIPLE',False).lower() in ('true', '1', 't', 'y', 'yes')),
        'SMB_DEBUG_MODE': bool(getenv('SMB_DEBUG_MODE', False).lower() in ('true', '1', 't', 'y', 'yes')),

        'SMB_LOAD_TO_PATH': getenv('SMB_LOAD_TO_PATH'),
        'SMB_LOAD_FILE_PATTERN': getenv('SMB_LOAD_FILE_PATTERN'),


        'CSV_DELIMITER': getenv('CSV_DELIMITER'),
        'CSV_DATA_INVALID_EAN13': getenv('CSV_DATA_INVALID_EAN13', False).lower() in ('true', '1', 't', 'y', 'yes'),
        'CSV_DATA_MAX_WIDTH': int(getenv('CSV_DATA_MAX_WIDTH', 200)),
        'CSV_DATA_INVALID_COMPOUND_PATH': getenv('CSV_DATA_INVALID_COMPOUND_PATH'),


        'LOG_PATH': getenv('LOG_PATH', 'logs'),
        'LOG_FILE': getenv('LOG_FILE'),
        'LOG_LEVEL_CONSOLE': getenv('LOG_LEVEL_CONSOLE', 'WARNING'),
        'LOG_LEVEL_FILE': getenv('LOG_LEVEL_FILE', 'WARNING'),


        'CHECK_INTERVAL': int(getenv('CHECK_INTERVAL', 60)),  # по умолчанию 60 секунд
        'WORKING_HOURS_START': getenv('WORKING_HOURS_START'),
        'WORKING_HOURS_END': getenv('WORKING_HOURS_END'),

        'STATUS_FILE_PATH': getenv('STATUS_FILE_PATH', 'status.log'),
    }


def get_db_config() -> dict:
    """
    Получение конфигурации для подключения к MySQL.
    """
    env = load_env()
    return {
        'host': env['DB_HOST'],
        'port': env['DB_PORT'],
        'user': env['DB_USER'],
        'password': env['DB_PASSWORD'],
        'database': env['DB_NAME'],
        'db_schemas_path': env['DB_SCHEMAS_PATH'],
        'db_file_init_schema': env['DB_FILE_INIT_SCHEMA'],
        'db_file_table_prefix': env['DB_FILE_TABLE_PREFIX'],
        'db_file_init_data_prefix': env['DB_FILE_INIT_DATA_PREFIX'],
    }


def get_smb_config() -> dict:
    """
    Получение конфигурации для доступа к SMB.
    """
    env = load_env()
    return {
        'hosts': env['SMB_HOSTS'].replace(' ', '').split(','),
        # 'host': env['SMB_HOST'],
        'user': env['SMB_USER'],
        'password': env['SMB_PASSWORD'],
        'port': env['SMB_PORT'],
        'timeout': env['SMB_TIMEOUT'],
        'host_template': env['SMB_HOSTNAME_TEMPLATE'],
        'share': env['SMB_SHARE'],
        'smb_path': env['SMB_PATH'],
        'to_path': env['SMB_LOAD_TO_PATH'],
        'file_pattern': env['SMB_LOAD_FILE_PATTERN'],
        'multiple': env['SMB_MULTIPLE'],
        'debug_mode': env['SMB_DEBUG_MODE'],

    }


def get_csv_config() -> dict:
    """
    Получение парамметров для CSV.
    """
    env = load_env()
    return {
        'csv_delimiter': env['CSV_DELIMITER'],
        'invalid_ean13': bool(env['CSV_DATA_INVALID_EAN13']),
        'max_width': int(env['CSV_DATA_MAX_WIDTH']),
        'invalid_compound_dir': env['CSV_DATA_INVALID_COMPOUND_PATH'],
        'log_path': env['LOG_PATH']

    }


def get_log_config() -> dict:
    """
    Получение конфигурации для логгера.
    """
    env = load_env()
    return {
        'path': join(env['LOG_PATH'], dt.now().strftime(env['LOG_FILE'])),
        'level_console': env['LOG_LEVEL_CONSOLE'],
        'level_file': env['LOG_LEVEL_FILE'],
    }


def get_status_config() -> dict:
    """
    Получение пути до файла статусов серверов.
    """
    env = load_env()
    return {
        'path': env['STATUS_FILE_PATH'],
    }


def get_schedule_config() -> dict:
    """
    Получение конфигурации для расписания задач (время выполнения, нерабочие часы).
    """
    env = load_env()
    return {
        'check_interval': env['CHECK_INTERVAL'],
        'working_hours_start': env['WORKING_HOURS_START'],
        'working_hours_end': env['WORKING_HOURS_END'],
    }


if __name__ == '__main__':
    print('Database Config:', get_db_config())
    print('SMB Config:', get_smb_config())
    print('Schedule Config:', get_schedule_config())
