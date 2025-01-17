__author__ = 'InfSub'
__contact__ = 'ADmin@TkYD.ru'
__copyright__ = 'Copyright (C) 2024, [LegioNTeaM] InfSub'
__date__ = '2024/01/17'
__deprecated__ = False
__email__ = 'ADmin@TkYD.ru'
__maintainer__ = 'InfSub'
__status__ = 'Production'
__version__ = '2.8.3'

# from pprint import pprint
from typing import Dict, Optional, Union
from os import remove as os_remove
from os.path import join as os_join, getsize as os_getsize, getmtime as os_getmtime
from pathlib import Path
from asyncio import sleep as aio_sleep, get_event_loop, to_thread as aio_to_thread
from aiofiles import open as aio_open
from concurrent.futures import ThreadPoolExecutor
from fnmatch import fnmatch
from ping3 import ping
from errno import EACCES as ERRNO_EACCES
from smbclient import ClientConfig, listdir, open_file
# from smb.SMBConnection import SMBConnection
from smbprotocol.exceptions import SMBConnectionClosed

from logger import logging, setup_logger  # импортируем наш модуль с настройками логгера
from make_dir import make_dir

setup_logger()
logger = logging.getLogger(__name__)


class SmbHandler:
    def __init__(self, config: Dict[str, Union[str, bool]]) -> None:
    # def __init__(self, server: str, username: str, password: str) -> None:
    #     """
    #     for ver.: 2.8.x:
    #     Инициализирует экземпляр класса SmbHandler с необходимыми параметрами для подключения к SMB-серверу.
    #
    #     :param server: Адрес или имя SMB-сервера.
    #     :type server: str
    #     :param username: Имя пользователя для аутентификации на сервере.
    #     :type username: str
    #     :param password: Пароль для аутентификации на сервере.
    #     :type password: str
    #     :return: None
    #     """
        """
        for ver.: 2.9.x:
        Инициализирует экземпляр класса SmbHandler с параметрами для подключения к SMB-серверу.

        :param config: Словарь с параметрами конфигурации.
        :type config: Dict[str, Union[str, bool]]

        config: Словарь с параметрами конфигурации, включающий:
            - 'server': адрес или имя SMB-сервера (str),
            - 'username': имя пользователя для аутентификации на сервере (str),
            - 'password': пароль для аутентификации на сервере (str),
            - 'share': название сетевой шары (str),
            - 'remote_path': удаленный путь к файлам (str),
            - 'file_pattern': шаблон для поиска файлов (str),
            - 'download_path': локальный путь для сохранения файлов (str),
            - 'download_file_name': имя файла для сохранения (str).

        :return: None
        """
        try:
            self.server: str = config['host']
            self.port: str = config['port']
            self.username: str = config['username']
            self.password: str = config['password']
            self.share: str = config['share']
            self.remote_path: str = config['remote_path']
            self.file_pattern: str = config['file_pattern']
            self.download_path: str = config['download_path']
            self.download_file_name: str = config['download_file_name']
            self.debug_mode: bool = config['debug_mode']
        except KeyError as e:
            logger.error(f'Missing configuration key: {e}')

        self.network_path = None
        self.max_retries: int = 3  # Максимальное количество попыток
        self.connection: bool = None  # Изначально соединение не установлено.
    
    async def connect_and_prepare(self) -> bool:
        if not await self.async_ping():
            logger.warning(f'Хост: {self.server} - недоступен.')
            return False
        
        logger.info(f'Хост: {self.server} - доступен. Подключение к сетевой шаре {self.share} ...')
        self.network_path = await self.create_network_path_async()
        return True

    async def connect(self, network_path: str = None) -> bool:
        """
        Устанавливает соединение с заданным сетевым путем.

        Метод пытается установить соединение с указанным сетевым путем. Если во время
        попытки соединения возникает ошибка, она логируется, и метод возвращает False.

        :param network_path: Путь к сетевой директории, с которой нужно установить соединение.
        :type network_path: str, optional

        :return: True, если соединение успешно установлено, иначе False.
        :rtype: bool

        :raises ValueError: Если сетевой путь не указан.
        :raises Exception: Логирует ошибку при возникновении ошибки соединения.
        """
        network_path = network_path if network_path is not None else self.network_path
        if not network_path:
            if not self.debug_mode:
                logger.error('Не указан сетевой путь.')
            else:
                raise ValueError('Не указан сетевой путь.')
        
        # Конфигурируем клиента с предоставленными учетными данными.
        # logger.warning(f'ClientConfig(username={self.username}, password={self.password})')
        ClientConfig(username=self.username, password=self.password)
        
        try:
            # # Создаем SMB соединение.
            # smb_connection = SMBConnection(self.username, self.password, 'client_machine', self.server)
            # connected = await aio_to_thread(smb_connection.connect, network_path, self.port)
            # if connected:
            #     self.connection = smb_connection
            #     logger.info(f'Successfully connected to {network_path}')

            listdir(network_path)  # Пытаемся получить список файлов, чтобы проверить доступность.
            self.connection = True  # Устанавливаем флаг, что соединение успешное.
            logger.info(f'Successfully connected to {network_path}')
            return True
        except Exception as e:
            logger.error(f'Error connecting to {network_path}: {e}')
            return False
    
    async def disconnect(self) -> None:
        """
        Завершает текущее соединение, если оно установлено.

        Если соединение установлено, устанавливает `self.connection` в None и логирует успешное завершение.
        Если соединение не было установлено, выдает предупреждение в лог о попытке закрытия несуществующего соединения.

        :return: None
        """
        if self.connection:
            # Здесь может быть добавлена дополнительная логика для корректного завершения соединения.
            logger.info('Connection closed')
            self.connection = None
        else:
            logger.warning('Attempt to close non-existent connection')

    async def async_ping(self, host: str = None) -> bool:
        """
        Асинхронно проверяет доступность указанного хоста посредством операции пинг и возвращает результат проверки.

        Этот метод выполняет операцию пинг в отдельном потоке, используя `ThreadPoolExecutor`, чтобы избежать
        блокировки основного потока событий. Результат выполнения операции пинг преобразуется в булево значение:
        True, если пинг успешен, и False, если неудачен.

        :param host: (optional) Адрес хоста, доступность которого необходимо проверить. Если не указан, используется
            адрес сервера, заданный при инициализации.
        :return: Булево значение, указывающее на доступность хоста: True, если доступен, иначе False.
        """
        if host is None:
            host = self.server
    
        loop = get_event_loop()
        with ThreadPoolExecutor() as executor:
            response = await loop.run_in_executor(executor, ping, host)
        return bool(response)
    
    async def create_network_path_async(self, host: str = None, share: str = None, path: str = None) -> str:
        """
        Асинхронно формирует строку сетевого пути на основе указанного сервера, общего ресурса и, при необходимости,
        подкаталога. Если путь не указан, метод составит сетевой путь только до общего ресурса на сервере.

        :param host: Альтернативное имя сервера; если не указано, используется значение, переданное в объекте при
            создании.
        :type host: str, optional
        :param share: Название общего ресурса, к которому требуется доступ.
        :type share: str, optional
        :param path: Опциональный подкаталог в общем ресурсе; если не указан, он будет исключен из пути.
        :type path: str, optional
        :return: Сформированный полный сетевой путь в формате UNC.
        :rtype: str
        :raises ValueError: Если не указаны обязательные параметры host или share.
        """
        host = host if host is not None else self.server
        if not host:
            if not self.debug_mode:
                logger.error('Не указано имя сервера.')
            else:
                raise ValueError('Не указано имя сервера.')
        
        share = share if share is not None else self.share
        if not share:
            if not self.debug_mode:
                logger.error('Не указано название общего ресурса.')
            else:
                raise ValueError('Не указано название общего ресурса.')
        
        path = path if path is not None else self.remote_path
        
        network_path = fr'\\{host}\{share}'
        if path:
            network_path += fr'\{path}'
        
        return network_path
    
    @staticmethod
    def _find_file_by_pattern(directory: str, file_pattern: str) -> Union[str, None]:
        """
        Ищет файл в указанной директории по заданному шаблону. Возвращает имя файла, если найден,
        иначе возвращает None.

        :param directory: Путь к директории, в которой осуществляется поиск файла.
        :type directory: str
        :param file_pattern: Шаблон имени файла, который необходимо найти.
        :type file_pattern: str
        :return: Имя найденного файла или None, если файл не найден.
        :rtype: Union[str, None]

        Иcключения:
        :raises OSError: Возникает при ошибке доступа к директории.

        Пример использования:

        .. code-block:: python

            найденный_файл = _find_file_by_pattern('/путь/к/директории', '*.txt')
            if найденный_файл:
                print(f'Файл найден: {найденный_файл}')
            else:
                print('Файл не найден')
        """
        try:
            dir_entries = listdir(directory)
            for entry in dir_entries:
                if fnmatch(entry, file_pattern):
                    return entry
        except Exception as e:
            logger.error(f'Error accessing {directory}: {e}')
        return None
    
    async def copy_files(self, host: Optional[str] = None, network_path: Optional[str] = None,
            file_pattern: Optional[str] = None, download_path: Optional[str] = None,
            download_file_name: Optional[str] = None) -> Union[str, bool]:
        """
        Асинхронно копирует файл с удаленного сервера на локальную машину.

        :param host: Название сервера. Если не указано, используется значение self.server.
        :type host: Optional[str]
        :param network_path: Путь к удаленной директории. Если не указано, используется значение self.network_path.
        :type network_path: Optional[str]
        :param file_pattern: Шаблон поиска файла. Если не указано, используется значение self.file_pattern.
        :type file_pattern: Optional[str]
        :param download_path: Локальный путь для сохранения файла. Если не указано, используется значение self.download_path.
        :type download_path: Optional[str]
        :param download_file_name: Имя файла для сохранения. Если не указано, используется значение self.download_file_name.
        :type download_file_name: Optional[str]

        :return: Путь к сохраненному файлу, если копирование успешно, иначе False.
        :rtype: Union[str, bool]

        :raises OSError: В случае проблем с файловой системой.
        :raises PermissionError: Если нет доступа к файлам на сетевом пути.
        :raises SMBConnectionClosed: Если соединение с сетевым ресурсом было закрыто.

        Метод выполняет следующие действия:
            - Проверяет указанный путь host, если он не был задан.
            - Создает директорию для загрузки, если она еще не существует.
            - Ищет файлы в указанной сетевой директории, соответствующие заданному шаблону.
            - Копирует каждый файл в указанное местоположение на локальном диске.
            - Обрабатывает ошибки, такие как проблемы с доступом к файлам или сетевые ошибки, пытаясь повторить операцию.
            - Логирует процесс копирования и возникновение ошибок.
        """
        if host is None:
            host = self.server
            
        if network_path is None:
            network_path = self.network_path
            
        if file_pattern is None:
            file_pattern = self.file_pattern
            
        if download_path is None:
            download_path = self.download_path
            
        if download_file_name is None:
            download_file_name = self.download_file_name
        
        file_path = os_join(download_path, download_file_name)
        await make_dir(os_join(Path.cwd(), download_path))
        
        try:
            # ver.: 2.8.1
            # # Получение списка файлов в указанной директории
            # dir_entries = listdir(network_path)
            #
            # # Открытие файла для записи (асинхронно)
            # async with aio_open(file_path, mode='wb') as dest_file:
            #     for entry in dir_entries:
            #         # Проверка, соответствует ли имя файла шаблону
            #         if fnmatch(entry, file_pattern):
            #             src_file_path = os_join(network_path, entry)  # Полный путь к исходному файлу
            
            entry = self._find_file_by_pattern(network_path, file_pattern)
            if entry is None:
                logger.warning(f'{host}: No file found matching pattern "{file_pattern}".')
                return False

            src_file_path = os_join(network_path, entry)
            async with aio_open(file_path, mode='wb') as dest_file:
                logger.info(f'{host}: Copying "{entry}" to "{Path(file_path).name}"')
                
                attempt = 0
                file_written = False  # Инициализация переменной

                while attempt < self.max_retries:
                    try:
                        # Открытие исходного файла через SMB
                        with open_file(src_file_path, mode='rb') as src_file:
                            # Чтение и запись файла по частям (chunk)
                            while chunk := src_file.read(4096):
                                await dest_file.write(chunk)
                                file_written = True
                        break  # Если успешный, выйти из цикла попыток
                    
                    except (SMBConnectionClosed, PermissionError, OSError) as e:
                        attempt += 1
                        if not await self._handle_retry(host, e, attempt, src_file_path):
                            return False
                    except Exception as e:
                        logger.error(f'{host}: An unexpected error occurred: {e}')
                        return False

                # Проверка, был ли файл успешно записан
                if file_written:
                    if os_getsize(file_path) > 0:
                        logger.info(f'{host}: Copying complete.')
                        return file_path  # Возврат пути к сохранённому файлу
                    else:
                        logger.warning(f'{host}: The copied file is empty.')
                        os_remove(file_path)  # Удаление пустого файла
                        return False
                else:
                    logger.warning(f'{host}: Failed to copy file.')
                    os_remove(file_path)  # Удаление пустого файла
                    return False
        
        except Exception as e:
            logger.error(f'{host}: Error accessing {network_path}: {e}')
            return False

    async def _handle_retry(
            self, error: Exception, attempt: int, src_file_path: str, host: str = None, max_retries: int = None) -> bool:
        """
        Обрабатывает повторные попытки при возникновении ошибок, связанных с доступом к файлам на SMB-сервере.

        :param error: Исключение, которое произошло в процессе попытки.
        :type error: Exception
        :param attempt: Номер текущей попытки, начиная с 1.
        :type attempt: int
        :param src_file_path: Путь к исходному файлу на сервере, для которого производится попытка.
        :type src_file_path: str
        :param host: Альтернативное имя или hostname SMB-сервера; используется, если отличается от self.server.
            По умолчанию None.
        :type host: str, optional
        :param max_retries: Максимальное количество попыток; используется, если отличается от self.max_retries.
            По умолчанию None.
        :type max_retries: int, optional

        :return: True, если стоит продолжить попытки, иначе False.
        :rtype: bool
        """
        if host is None:
            host = self.server
            
        if max_retries is None:
            max_retries = self.max_retries
        
        if error.errno == ERRNO_EACCES:
            logger.error(f'{host}: File is being used by another process: {src_file_path}')
        
        logger.warning(f'{host}: Attempt {attempt} failed with error: {error}')
        
        if attempt >= max_retries:
            logger.error(f'{host}: Exhausted {max_retries} retries for file: {src_file_path}')
            return False
        else:
            # Задержка перед повторной попыткой с увеличением времени между попытками
            wait_time = 2 ** attempt
            logger.warning(f'{host}: Waiting {wait_time} seconds for file: {src_file_path}')
            await aio_sleep(wait_time)
            return True

    # TODO: Требуется добавить имя файла на удаленном сервере (полученное по шаблону)
    async def file_has_been_updated(
            self, network_path: Optional[str] = None, local_file_path: Optional[str] = None, file_name: Optional[str]
            = None) -> bool:
        """
        Проверяет, обновился ли файл на удаленном сервере с момента последнего копирования на локальный диск.

        :param network_path: Сетевой путь к директории на сервере.
        :type network_path: str, optional
        :param local_file_path: Путь к локальному файлу, с которым сравнивается удаленный.
        :type local_file_path: str, optional
        :param file_name: Имя файла для проверки.
        :type file_name: str, optional
        
        :return: True, если файл на сервере был обновлён, иначе False.
        :rtype: bool
        """
        if network_path is None:
            network_path = self.network_path
            
        if local_file_path is None:
            local_file_path = self.download_path

        if file_name is None:
            file_name = self.download_file_name
            
        try:
            remote_file_path = os_join(network_path, file_name)
            local_file_mtime = os_getmtime(local_file_path)
            
            logger.warning(f'remote_file_path: {remote_file_path} | local_file_path: {local_file_path}')
            
            with open_file(remote_file_path, mode='rb') as remote_file:
                remote_file_mtime = remote_file.last_write_time
            
            logger.info(f'Comparing modification times: local {local_file_mtime}, remote {remote_file_mtime}')
            return remote_file_mtime > local_file_mtime
        
        except FileNotFoundError:
            logger.error(f'File not found: {local_file_path} or {remote_file_path}')
            return False
        
        except PermissionError as e:
            if e.errno == ERRNO_EACCES:
                logger.error(f'Permission denied: {local_file_path} or {remote_file_path}')
            return False
        
        except Exception as e:
            logger.error(f'Error checking file update status for {file_name}: {e}')
            return False
