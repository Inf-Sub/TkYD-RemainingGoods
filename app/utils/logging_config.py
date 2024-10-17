__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/10/04'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.1.5'


import logging
import logging.config
import aiofiles
import asyncio
from colorlog import ColoredFormatter

from app.config import LOG_PATH, LOG_LEVEL_CONSOLE, LOG_LEVEL_FILE


class AsyncFileHandler(logging.Handler):
    def __init__(self, filename):
        logging.Handler.__init__(self)
        self.filename = filename

    async def _write_log(self, message):
        async with aiofiles.open(self.filename, 'a') as log_file:
            await log_file.write(message + '\n')

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self._write_log(log_entry))


def setup_logging(log_file=LOG_PATH):
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s\t\t%(name)s\t%(levelname)s:\t%(message)s",
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
                'format': '%(asctime)s\t\t%(name)s\t%(levelname)s:\t%(message)s'
            },
            'colored': {
                '()': ColoredFormatter,
                'format': "%(log_color)s%(asctime)s\t\t%(name)s\t%(levelname)s:\t%(message)s",
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
                'level': LOG_LEVEL_CONSOLE,
            },
            'async_file': {
                '()': AsyncFileHandler,
                'formatter': 'standard',
                'level': LOG_LEVEL_FILE,
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
            'level': 'DEBUG',
        },
    })


if __name__ == '__main__':
    # Вызов функции настройки логгера при импорте модуля
    setup_logging(LOG_PATH)
