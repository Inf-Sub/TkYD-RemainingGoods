__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/12/22'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.8.2'

import logging
import logging.config
from aiofiles import open as aio_open
from asyncio import create_task as aio_create_task
from colorlog import ColoredFormatter
from pathlib import Path
from typing import List, Optional

from config import get_log_config


class AsyncFileHandler(logging.Handler):
    """Asynchronous file handler for logging, allowing log messages to be written to a file asynchronously."""
    
    def __init__(self, filename: str) -> None:
        """
        Initialize the AsyncFileHandler with the specified filename.

        Args:
            filename (str): The name of the file to which logs will be written.
            
        Returns:
            None
        """
        super().__init__()
        self.filename = filename
    
    async def _write_log(self, message: str) -> None:
        """
        Asynchronously writes a log message to a file.

        Args:
            message (str): The log message to write.
            
        Returns:
            None
        """
        async with aio_open(self.filename, 'a') as log_file:
            await log_file.write(message + '\n')
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Formats and dispatches a log record by creating an asynchronous task.

        Args:
            record (logging.LogRecord): The log record to format and dispatch.
            
        Returns:
            None
        """
        log_entry = self.format(record)
        aio_create_task(self._write_log(log_entry))


def setup_logger(log_file: Optional[str] = None) -> None:
    """
    Configures the logging settings, including file paths and formats.

    Args:
        log_file (Optional[str]): The file path for logging; if not provided, it defaults to the environment setting.
        
        Returns:
            None
    """
    env = get_log_config()
    
    if log_file is None:
        log_file = env['path']
    
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)
    
    formatter = ColoredFormatter(
        '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
        datefmt=None, reset=True,
        log_colors={'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'bold_red', })
    
    logging.config.dictConfig({'version': 1, 'disable_existing_loggers': False, 'formatters': {'standard': {
        'format': '%(filename)s:%(lineno)d | %(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s'},
        'colored': {'()': ColoredFormatter,
                    'format': '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
                    'datefmt': None, 'reset': True,
                    'log_colors': {'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red',
                                   'CRITICAL': 'bold_red', }}}, 'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'colored', 'level': env['level_console'], },
        'rotating_file': {'class': 'logging.handlers.RotatingFileHandler', 'formatter': 'standard',
                          'level': env['level_file'], 'filename': log_file, 'maxBytes': 10 * 1024 * 1024,
                          'backupCount': 5, }, },
                               'root': {'handlers': ['console', 'rotating_file'], 'level': 'INFO', }, })
    
    log_ignore_list: List[str] = ['smbprotocol']
    
    for logger_name in log_ignore_list:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def change_log_levels(console_level: str, file_level: str) -> None:
    """
    Change the logging levels for console and file handlers.

    Args:
        console_level (str): The logging level for console output.
        file_level (str): The logging level for file output.
        
        Returns:
            None
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(console_level)
        elif isinstance(handler, logging.handlers.RotatingFileHandler):
            handler.setLevel(file_level)


if __name__ == '__main__':
    setup_logger()
    
    # Example on how to change log levels dynamically
    # This should be replaced with the actual logic for reading the new levels
    new_console_level = 'INFO'
    new_file_level = 'ERROR'
    change_log_levels(new_console_level, new_file_level)


# version 2.7.2

# import logging
# import logging.config
# from aiofiles import open as aio_open
# from asyncio import create_task as aio_create_task
# from colorlog import ColoredFormatter
# from pathlib import Path
# from config import get_log_config
# from typing import List
#
#
# class AsyncFileHandler(logging.Handler):
#     """Asynchronous file handler for logging."""
#
#     def __init__(self, filename: str):
#         super().__init__()
#         self.filename = filename
#
#     async def _write_log(self, message: str) -> None:
#         """Asynchronously writes a log message to a file."""
#         async with aio_open(self.filename, 'a') as log_file:
#             await log_file.write(message + '\n')
#
#     def emit(self, record: logging.LogRecord) -> None:
#         """Formats and dispatches a log record."""
#         log_entry = self.format(record)
#         aio_create_task(self._write_log(log_entry))
#
#
# def setup_logger(log_file: str = None) -> None:
#     """Configures the logging settings."""
#     env = get_log_config()
#
#     if log_file is None:
#         log_file = env['path']
#
#     log_path = Path(log_file).parent
#     log_path.mkdir(parents=True, exist_ok=True)
#
#     formatter = ColoredFormatter(
#         '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
#         datefmt=None, reset=True,
#         log_colors={
#             'DEBUG': 'cyan',
#             'INFO': 'green',
#             'WARNING': 'yellow',
#             'ERROR': 'red',
#             'CRITICAL': 'bold_red',
#         })
#
#     logging.config.dictConfig({
#             'version': 1,
#             'disable_existing_loggers': False,
#             'formatters': {
#                 'standard': {
#                     'format': '%(filename)s:%(lineno)d | %(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s'},
#                 'colored': {
#                     '()': ColoredFormatter,
#                     'format': '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %(message)s',
#                     'datefmt': None,
#                     'reset': True,
#                     'log_colors': {
#                         'DEBUG': 'cyan',
#                         'INFO': 'green',
#                         'WARNING': 'yellow',
#                         'ERROR': 'red',
#                         'CRITICAL': 'bold_red',
#                     }
#                 }
#             },
#         'handlers': {
#             'console': {
#                 'class': 'logging.StreamHandler',
#                 'formatter': 'colored',
#                 'level': env['level_console'],
#             },
#             'rotating_file': {
#                 'class': 'logging.handlers.RotatingFileHandler',
#                 'formatter': 'standard',
#                 'level': env['level_file'],
#                 'filename': log_file,
#                 'maxBytes': 10 * 1024 * 1024,
#                 'backupCount': 5,
#             },
#         },
#         'root': {
#             'handlers': ['console', 'rotating_file'],
#             'level': 'INFO',
#         },
#     })
#
#     log_ignore_list: List[str] = ['smbprotocol']
#
#     for logger_name in log_ignore_list:
#         logging.getLogger(logger_name).setLevel(logging.WARNING)
#
#
# if __name__ == '__main__':
#     setup_logger()


# version '2.5.3'

# import logging
# import logging.config
# from aiofiles import open as aio_open
# from asyncio import create_task as aio_create_task
# from colorlog import ColoredFormatter
# from pathlib import Path
#
# from config import get_log_config
#
#
# class AsyncFileHandler(logging.Handler):
#     def __init__(self, filename):
#         logging.Handler.__init__(self)
#         self.filename = filename
#
#     async def _write_log(self, message):
#         async with aio_open(self.filename, 'a') as log_file:
#             await log_file.write(message + '\n')
#
#     def emit(self, record):
#         log_entry = self.format(record)
#         aio_create_task(self._write_log(log_entry))
#
#
# def setup_logger(log_file: str = get_log_config()['path']):
#     env = get_log_config()
#
#     log_path = Path(env['path']).parent
#     if not log_path.exists():
#         log_path.mkdir(parents=True, exist_ok=False)
#
#     formatter = ColoredFormatter(
#         # '%(log_color)s%(asctime)s\t\t%(name)s\t%(levelname)s:\t%(message)s',
#         '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %(funcName)-28s| %('
#         'message)s',
#         datefmt=None,
#         reset=True,
#         log_colors={
#             'DEBUG': 'cyan',
#             'INFO': 'green',
#             'WARNING': 'yellow',
#             'ERROR': 'red',
#             'CRITICAL': 'bold_red',
#         }
#     )
#
#     logging.config.dictConfig({
#         'version': 1,
#         'disable_existing_loggers': False,  # False
#         'formatters': {
#             'standard': {
#                 # 'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#                 # 'format': '%(asctime)-25s%(name)-16s%(levelname)-10s%(message)s'
#                 'format': '%(filename)s:%(lineno)d | %(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %('
#                           'funcName)-28s| %(message)s'
#             },
#             'colored': {
#                 '()': ColoredFormatter,
#                 # 'format': '%(log_color)s%(asctime)-25s%(name)-16s%(levelname)-10s%(message)s',
#                 'format': '%(filename)s:%(lineno)d\n%(log_color)s%(asctime)-24s| %(levelname)-8s| %(name)-12s\t| %('
#                           'funcName)-28s| %(message)s',
#                 'datefmt': None,
#                 'reset': True,
#                 'log_colors': {
#                     'DEBUG': 'cyan',
#                     'INFO': 'green',
#                     'WARNING': 'yellow',
#                     'ERROR': 'red',
#                     'CRITICAL': 'bold_red',
#                 }
#             }
#         },
#         'handlers': {
#             'console': {
#                 'class': 'logging.StreamHandler',
#                 # 'formatter': 'standard',
#                 'formatter': 'colored',
#                 'level': env['level_console'],
#             },
#             'async_file': {
#                 '()': AsyncFileHandler,
#                 'formatter': 'standard',
#                 'level': env['level_file'],
#                 'filename': log_file,
#             },
#             # 'file': {
#             #     'class': 'logging.FileHandler',
#             #     'formatter': 'standard',
#             #     # 'level': 'DEBUG',
#             #     'level': 'INFO',
#             #     'filename': log_file,
#             # },
#         },
#         'root': {
#             # 'handlers': ['console', 'file'],
#             'handlers': ['console', 'async_file'],
#             'level': 'INFO',  # Устанавливаем уровень для корневого логгера
#         },
#     })
#
#     log_ignore_list = ['smbprotocol']
#
#     # Устанавливаем уровень логирования для библиотек на WARNING
#     for name in list(logging.root.manager.loggerDict.keys()):
#         if name != 'root':
#             if name in log_ignore_list:
#                 logging.getLogger(name).setLevel(logging.WARNING)
#
#             # Устанавливаем уровень логирования для логгера в нашем коде
#             logging.getLogger(__name__).setLevel(logging.DEBUG)
#
#
# if __name__ == '__main__':
#     # Вызов функции настройки логгера при импорте модуля
#     setup_logger()
