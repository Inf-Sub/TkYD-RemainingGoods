__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/11/27'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.5.2'


import logging
import logging.config
from aiofiles import open as aio_open
from asyncio import create_task as aio_create_task
from colorlog import ColoredFormatter
from pathlib import Path

from config import get_log_config


class AsyncFileHandler(logging.Handler):
    def __init__(self, filename):
        logging.Handler.__init__(self)
        self.filename = filename

    async def _write_log(self, message):
        async with aio_open(self.filename, 'a') as log_file:
            await log_file.write(message + '\n')

    def emit(self, record):
        log_entry = self.format(record)
        aio_create_task(self._write_log(log_entry))


def setup_logger(log_file: str = get_log_config()['path']):
    env = get_log_config()

    log_path = Path(env['path']).parent
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=False)

    formatter = ColoredFormatter(
        # '%(log_color)s%(asctime)s\t\t%(name)s\t%(levelname)s:\t%(message)s',
        '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # False
        'formatters': {
            'standard': {
                # 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                # 'format': '%(asctime)-25s%(name)-16s%(levelname)-10s%(message)s'
                'format': '%(filename)s:%(lineno)d | %(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s'
            },
            'colored': {
                '()': ColoredFormatter,
                # 'format': '%(log_color)s%(asctime)-25s%(name)-16s%(levelname)-10s%(message)s',
                'format': '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
                'datefmt': None,
                'reset': True,
                'log_colors': {
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                # 'formatter': 'standard',
                'formatter': 'colored',
                'level': env['level_console'],
            },
            'async_file': {
                '()': AsyncFileHandler,
                'formatter': 'standard',
                'level': env['level_file'],
                'filename': log_file,
            },
            # 'file': {
            #     'class': 'logging.FileHandler',
            #     'formatter': 'standard',
            #     # 'level': 'DEBUG',
            #     'level': 'INFO',
            #     'filename': log_file,
            # },
        },
        'root': {
            # 'handlers': ['console', 'file'],
            'handlers': ['console', 'async_file'],
            'level': 'INFO',  # Устанавливаем уровень для корневого логгера
        },
    })

    log_ignore_list = ['smbprotocol']

    # Устанавливаем уровень логирования для библиотек на WARNING
    for name in list(logging.root.manager.loggerDict.keys()):
        if name != 'root':
            if name in log_ignore_list:
                logging.getLogger(name).setLevel(logging.WARNING)

            # Устанавливаем уровень логирования для логгера в нашем коде
            logging.getLogger(__name__).setLevel(logging.DEBUG)


if __name__ == '__main__':
    # Вызов функции настройки логгера при импорте модуля
    setup_logger()
