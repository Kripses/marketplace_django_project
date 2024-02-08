from datetime import datetime
import json
import io
from os import path, PathLike
from typing import Union
import zipfile

from django.core.exceptions import PermissionDenied
from django.core.files.images import ImageFile
from django.db import transaction
from django.utils.text import slugify

from .import_utils import ImportLogger, FileManager
from .mailer import send_email
from account.models import Profile, Seller
from products.models import (
    Category,
    ImportStatusEnum,
    Picture,
    Product,
    SellerProduct,
)


class ProductImporter:
    def __init__(
            self,
            file: Union[str, PathLike[str], bytes],
            user_id: int = None,
            email: str = None,
    ):
        self.__user_id = user_id
        self.__email = email
        self.__original_path = None
        self.__target_path = None
        self.__filename = None
        self.__json = None
        self.__start = datetime.now()
        self.__file_manager = FileManager(self.__start)
        self.__logger = ImportLogger(self.__start, self.__file_manager)
        self.__product_imports = 0
        self.__successful_product_imports = 0
        self.__image_imports = 0
        self.__successful_image_imports = 0
        self.__seller_product_imports = 0
        self.__successful_seller_product_imports = 0
        self.__total_imports = 0
        self.__successful_imports = 0

        self.__import_products(file)

    def __import_products(self, file: Union[str, PathLike[str], bytes]):
        try:
            if self.__user_id:
                self.__initiating_user = Profile.objects.filter(
                    pk=self.__user_id
                ).first()
                self.__logger.log(
                    'Begin product import initiated by user {pk} | {username} | {email}'.format(
                        pk=self.__initiating_user.pk,
                        username=self.__initiating_user.username,
                        email=self.__initiating_user.email,
                    )
                )
            else:
                self.__logger.log('Begin product_import initiated by admin')
            self.__check_file(file)
            self.__check_archive()
            self.__add_entries_from_archive_to_database()
            self.__logger.log('Import finished')

            self.__calculate_successful_imports()
            if self.__successful_imports:
                self.__logger.log_result(
                    self.__successful_imports,
                    self.__product_imports,
                    self.__successful_product_imports,
                    self.__image_imports,
                    self.__successful_image_imports,
                    self.__seller_product_imports,
                    self.__successful_seller_product_imports,
                )
        except Exception as e:
            self.__logger.log(f'Import failed due to {type(e).__name__}: {e}')
            self.__successful_imports = 0
        finally:
            self.__calculate_total_imports()
            status = self.__get_status()
            log = self.__logger.finalize_log(status, self.__successful_imports)

            success = self.__successful_imports > 0
            if self.__json:
                file_path = self.__file_manager.get_json_path(success)
                file = self.archive.read(self.__json)
                self.__file_manager.save_file(file, file_path)
            if self.__original_path:
                self.__file_manager.remove_file(self.__original_path)

            self.__notify_admin(status, log)

    def __check_file(self, file: Union[str, PathLike[str], bytes]):
        if isinstance(file, PathLike) or isinstance(file, str):
            if path.exists(file) and path.isfile(file):
                self.file = file
                self.__original_path = file
        elif isinstance(file, bytes):
            self.file = io.BytesIO(file)
        else:
            raise ValueError('Not a viable file provided')

    def __check_archive(self):
        self.archive = zipfile.ZipFile(self.file)

        if self.archive.testzip():
            raise ImportError('There are corrupted files in the archive')

        self.__get_file_names_from_archive()

        self.__json = self.file_names.get('json')
        if not self.__json:
            raise FileNotFoundError('There is no json file in the archive')

    def __get_file_names_from_archive(self):
        self.file_names = {}
        for info in self.archive.infolist():
            if not info.is_dir():
                if info.filename.endswith('.json'):
                    if self.file_names.get('json'):
                        print('Too many json files')
                        raise ImportError('Too many json files')
                    self.file_names['json'] = info.filename
                else:
                    name_path = info.filename.split('/')
                    if len(name_path) != 3:
                        continue
                    self.file_names.setdefault(name_path[1], []).append(
                        info.filename,
                    )
        print(self.file_names)

    def __add_entries_from_archive_to_database(self):
        json_file = json.loads(self.archive.read(self.__json))
        self.products = json_file.get('products')
        self.seller_products = json_file.get('seller_products')

        with transaction.atomic():
            if self.products:
                self.__add_products_to_database()
            if self.seller_products:
                self.__add_seller_products_to_database()

    def __add_products_to_database(self):
        self.__logger.log(f'Importing products')
        self.new_products = {}

        for prod_name, prod_content in self.products.items():
            self.__add_product_to_database(prod_content, prod_name)

        if self.__successful_product_imports:
            self.__logger.log(f'Imported {self.__successful_product_imports} products')

    def __add_product_to_database(self, prod_content, prod_name):
        self.__product_imports += 1
        try:
            with transaction.atomic():
                prod_content['category'] = Category.objects.filter(
                    pk=prod_content['category'],
                ).first()
                if not prod_content.get('slug'):
                    prod_content['slug'] = slugify(prod_content['name'])
                new_product = Product(**prod_content)
                new_product.save()
                self.__successful_product_imports += 1
                self.new_products[prod_name] = new_product

                prod_images = self.file_names.get(prod_name)
                if prod_images:
                    self.__add_pictures_to_database(
                        prod_images,
                        new_product
                    )
                self.__logger.log(f'Product {prod_name} imported successfully')
        except Exception as e:
            self.__logger.log(
                f'Product ({prod_name}) product_import failed due to {type(e).__name__}: {e}'
            )

    def __add_pictures_to_database(
        self,
        prod_images,
        product
    ):
        self.__logger.log(f'Importing product images')
        for image_name in prod_images:
            self.__image_imports += 1
            try:
                with transaction.atomic():
                    name = path.basename(image_name)
                    image = ImageFile(
                        io.BytesIO(self.archive.read(image_name)),
                        name=name,
                    )
                    new_image = Picture(
                        product=product,
                        image=image,
                    )
                    new_image.save()
                    self.__successful_image_imports += 1
                    self.__logger.log(f'Image {image_name} imported successfully')
            except Exception as e:
                self.__logger.log(
                    f'Image ({image_name}) product_import failed due to {type(e).__name__}: {e}'
                )

    def __add_seller_products_to_database(self):
        self.__logger.log(f'Importing seller products')

        for sell_prod_name, sell_prod_data in self.seller_products.items():
            self.__add_seller_product_to_database(sell_prod_data, sell_prod_name)
        if self.__successful_seller_product_imports:
            self.__logger.log(
                f'Imported {self.__successful_seller_product_imports} seller products'
            )

    def __add_seller_product_to_database(self, sell_prod_data, sell_prod_name):
        self.__seller_product_imports += 1
        try:
            with transaction.atomic():
                self.__process_seller_product_params(sell_prod_data)
                new_seller_product = SellerProduct(**sell_prod_data)
                new_seller_product.save()
                self.__successful_seller_product_imports += 1
                self.__logger.log(f'Seller product {sell_prod_name} imported successfully')
        except Exception as e:
            self.__logger.log(
                f'Seller product ({sell_prod_name}) import failed due to {type(e).__name__}: {e}',
            )

    def __process_seller_product_params(self, sell_prod):
        sell_prod['seller'] = Seller.objects.filter(
            pk=sell_prod['seller'],
        ).select_related('profile').first()
        seller_owner = sell_prod['seller']
        if self.__user_id and not (seller_owner.pk == self.__user_id or
                                   seller_owner.is_admin or
                                   seller_owner.is_staff):
            raise PermissionDenied('Can\'t add products for someone else\'s seller')
        if sell_prod.get('new'):
            sell_prod['product'] = self.new_products[
                str(sell_prod['product'])]
        else:
            sell_prod['product'] = Product.objects.filter(
                pk=sell_prod['product'],
            ).first()

        if isinstance(sell_prod.get('new'), int):
            del sell_prod['new']

    def __calculate_successful_imports(self):
        self.__successful_imports = sum(
            (
                self.__successful_product_imports,
                self.__successful_image_imports,
                self.__successful_seller_product_imports,
            )
        )

    def __calculate_total_imports(self):
        self.__total_imports = sum(
            (
                self.__product_imports,
                self.__image_imports,
                self.__seller_product_imports,
            )
        )

    def __get_status(self):
        if not self.__successful_imports:
            return ImportStatusEnum.FAILURE
        if self.__successful_imports == self.__total_imports:
            return ImportStatusEnum.SUCCESS
        else:
            return ImportStatusEnum.PARTIAL_SUCCESS

    def __notify_admin(self, status, log):
        if self.__user_id:
            subject = 'Product import initiated by user {pk} | {username}'.format(
                pk=self.__initiating_user.pk,
                username=self.__initiating_user.username,
                email=self.__initiating_user.email,
            )
            message = """
Product import by user {pk} | {username} | {email} has been performed.
Import result: {status}.
Here's the log:
{log}
            """.format(
                pk=self.__initiating_user.pk,
                username=self.__initiating_user.username,
                email=self.__initiating_user.email,
                status=status.name,
                log=log
            )

            send_email(subject, message, self.__email)
