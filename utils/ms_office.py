import pandas as pd
import sys
import io
import msoffcrypto
from getpass import getpass

from loguru import logger
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError
from termcolor import cprint

from core.dataclasses import ExcelAccountData


def get_data_from_excel(
        file_path: str,
        page_name: str,
        data_class: type[ExcelAccountData],
        encrypted: bool = False,
) -> list[type[ExcelAccountData]]:
    try:
        decrypted_data = io.BytesIO()
        with open(file_path, 'rb') as file:
            if encrypted:
                cprint('⚔️ Enter the password degen', color='light_blue')
                password = getpass()
                office_file = msoffcrypto.OfficeFile(file)

                try:
                    office_file.load_key(password=password)
                except msoffcrypto.exceptions.DecryptionError:
                    cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️', color='light_red', attrs=["blink"])
                    raise DecryptionError('Incorrect password')

                try:
                    office_file.decrypt(decrypted_data)
                except msoffcrypto.exceptions.InvalidKeyError:
                    cprint('\n⚠️ Incorrect password to decrypt Excel file! ⚠️', color='light_red', attrs=["blink"])
                    raise InvalidKeyError('Incorrect password')
                except msoffcrypto.exceptions.DecryptionError:
                    cprint('\n⚠️ Set password on your Excel file first! ⚠️', color='light_red', attrs=["blink"])
                    raise DecryptionError('Excel file without password!')

                office_file.decrypt(decrypted_data)
            else:
                decrypted_data = file

            try:
                wb = pd.read_excel(decrypted_data, sheet_name=page_name)
            except ValueError as e:
                logger.error(e)
                cprint('\n⚠️ Wrong page name! Please check EXCEL_PAGE_NAME ⚠️', color='light_red', attrs=["blink"])
                raise ValueError(f"{e}")

            instances = []
            for index, row in wb.iterrows():
                instance = data_class.from_dataframe_row(row)
                instances.append(instance)

            return instances

    except (DecryptionError, InvalidKeyError, DecryptionError, ValueError) as e:
        logger.error(e)
        sys.exit()
