from datetime import datetime
import os

import celery
from django.conf import settings

from products.models import ProductImportLog


class ImportLogger:
    # TODO: добавить докстринг для чего этот сервис
    def __init__(self, start, file_manager):
        self.__log_messages = []
        self.__start = start
        self.__file_manager = file_manager
        self.__import_log = ProductImportLog(start=self.__start)
        self.__import_log.save()

    def log(self, message):
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
        successful_imports=0,
        product_imports=0,
        successful_product_imports=0,
        image_imports=0,
        successful_image_imports=0,
        seller_product_imports=0,
        successful_seller_product_imports=0,
    ):
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

    def finalize_log(self, status, import_count):
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
    def __init__(self, start):
        self.__start = start
        self.__filename = None

    @staticmethod
    def save_file(content, save_path):
        mode = 'wb' if isinstance(content, bytes) else 'w'

        with open(save_path, mode) as f:
            f.write(content)

    @staticmethod
    def remove_file(file_path):
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    def get_log_path(self):
        logs_dir = settings.IMPORT_LOGS_DIR

        return self.__get_file_path(logs_dir, 'log')

    def get_json_path(self, success):
        if success:
            target_dir = settings.IMPORT_SUCCESS_DIR
        else:
            target_dir = settings.IMPORT_FAILURE_DIR

        return self.__get_file_path(target_dir, 'json')

    def __get_file_path(self, target_dir, file_extension):
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

    def get_filename(self, extension=''):
        if not self.__filename:
            self.__filename = self.__start.strftime(
                '[%Y-%m-%d %H:%M:%S] - ',
            ) + celery.uuid()

        return self.__filename + '.' + extension if extension else self.__filename
