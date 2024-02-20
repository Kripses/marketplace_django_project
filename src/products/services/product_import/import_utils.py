from datetime import datetime
import os
from typing import Union

import celery
from django.conf import settings

from products.models import ProductImportLog


class ImportLogger:
    """ Класс, отвечающий за логгирование импорта товаров. """
    def __init__(self, start: datetime, file_manager: 'FileManager'):
        self.__log_messages = []
        self.__start = start
        self.__file_manager = file_manager
        self.__import_log = ProductImportLog(start=self.__start)
        self.__import_log.save()

    def log(self, message: str) -> None:
        """ Добавить сообщение в лог.

        Args:
            message (str): сообщение.
        """
        print(message)
        now = datetime.now()
        message = f'[{now.time()}] {message}'
        self.__log_messages.append(message)

        message_log = self.__import_log.message_log
        if not message_log:
            message_log = ''
        message_log = message_log + message + '\n'
        self.__import_log.message_log = message_log
        self.__import_log.save()

    def log_result(
        self,
        successful_imports: int = 0,
        product_imports: int = 0,
        successful_product_imports: int = 0,
        image_imports: int = 0,
        successful_image_imports: int = 0,
        seller_product_imports: int = 0,
        successful_seller_product_imports: int = 0,
    ) -> None:
        """
        Добавить в лог результат импорта.

        Args:
            successful_imports (int): общее количество успешно импортированных записей,
            product_imports (int): общее количество записей о продуктах для импорта,
            successful_product_imports (int): кол-во успешно импортированных записей о продуктах,
            image_imports (int): кол-во изображений для импорта,
            successful_image_imports (int): кол-во успешно импортированных изображений,
            seller_product_imports (int): кол-во записей seller_product для импорта,
            successful_seller_product_imports (int): кол-во успешно импортированных записей seller_product.
        """
        message = f'Successfully imported {successful_imports} items: '
        details = []
        if product_imports:
            details.append(
                '{success}/{total} products'.format(
                    success=successful_product_imports,
                    total=product_imports,
                ),
            )
        if image_imports:
            details.append(
                '{success}/{total} product images'.format(
                    success=successful_image_imports,
                    total=image_imports,
                ),
            )
        if seller_product_imports:
            details.append(
                '{success}/{total} seller products'.format(
                    success=successful_seller_product_imports,
                    total=seller_product_imports,
                ),
            )
        message = message + ', '.join(details)

        self.log(message)

    def finalize_log(
            self,
            status: 'ImportStatusEnum',
            import_count: int,
    ) -> str:
        """
        Завершить ведение лога и получить результат.

        Args:
            status (ImportStatusEnum): статус завершения процесса импорта,
            import_count (int): кол-во импортированных записей.

        Returns:
            str: Текст лога.
        """
        self.__import_log.end = datetime.now()
        self.__import_log.status = status
        self.__import_log.items_imported = import_count
        self.__import_log.file_name = self.__file_manager.get_filename()
        self.__import_log.save()

        log = '\n'.join(self.__log_messages)
        print(log)

        log_path = self.__file_manager.get_log_path()
        self.__file_manager.save_file(log, log_path)

        return log


class FileManager:
    """ Класс, отвечающий за операции с файлами в процессе импорта. """
    def __init__(self, start):
        self.__start = start
        self.__filename = None

    @staticmethod
    def save_file(content: Union[bytes, str], save_path: str) -> None:
        """
        Сохранить файл на диск.

        Args:
            content (Union[bytes, str]): содержимое файла,
            save_path (str): путь для сохранения файла.
        """
        mode = 'wb' if isinstance(content, bytes) else 'w'

        with open(save_path, mode) as f:
            f.write(content)

    @staticmethod
    def remove_file(file_path: str) -> None:
        """
        Удалить файл с диска.

        Args:
            file_path (str): путь к файлу.
        """
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    def get_log_path(self) -> str:
        """ Получить путь к файлу лога импорта на диске. """
        logs_dir = settings.IMPORT_LOGS_DIR

        return self.__get_file_path(logs_dir, 'log')

    def get_json_path(self, success: bool) -> str:
        """
        Получить путь к файлу json импорта на диске.

        Args:
             success (bool): был ли импорт успешным.
        """
        if success:
            target_dir = settings.IMPORT_SUCCESS_DIR
        else:
            target_dir = settings.IMPORT_FAILURE_DIR

        return self.__get_file_path(target_dir, 'json')

    def __get_file_path(self, target_dir: str, file_extension: str) -> str:
        """
        Получить путь для сохранения файлов текущего процесса импорта.

        Args:
            target_dir(str): путь до директории импорта,
            file_extension(str): расширение файла.
        """
        import_dir = settings.IMPORT_DIR
        if not os.path.exists(import_dir):
            os.mkdir(import_dir)

        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

        today_dir = target_dir.joinpath(datetime.now().strftime('%Y-%m-%d'))
        if not os.path.exists(today_dir):
            os.mkdir(today_dir)

        filename = self.get_filename(file_extension)
        return today_dir.joinpath(filename)

    def get_filename(self, extension: str = '') -> str:
        """ Получить имя для файла связанного с текущим процессом импорта. """
        if not self.__filename:
            self.__filename = self.__start.strftime(
                '[%Y-%m-%d %H:%M:%S] - ',
            ) + celery.uuid()

        return self.__filename + '.' + extension if extension else self.__filename
