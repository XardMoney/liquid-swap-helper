import pandas as pd
import sys
import io
import msoffcrypto
from getpass import getpass

from loguru import logger
from msoffcrypto.exceptions import DecryptionError, InvalidKeyError

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
                logger.success('⚔️ Enter the password degen')
                password = getpass()
                office_file = msoffcrypto.OfficeFile(file)

                try:
                    office_file.load_key(password=password)
                except msoffcrypto.exceptions.DecryptionError:
                    logger.error('\n⚠️ Incorrect password to decrypt Excel file! ⚠️')
                    raise DecryptionError('Incorrect password')

                try:
                    office_file.decrypt(decrypted_data)
                except msoffcrypto.exceptions.InvalidKeyError:
                    logger.error('\n⚠️ Incorrect password to decrypt Excel file! ⚠️')
                    raise InvalidKeyError('Incorrect password')
                except msoffcrypto.exceptions.DecryptionError:
                    logger.error('\n⚠️ Set password on your Excel file first! ⚠️')
                    raise DecryptionError('Excel file without password!')

                office_file.decrypt(decrypted_data)
            else:
                decrypted_data = file

            try:
                wb = pd.read_excel(decrypted_data, sheet_name=page_name)
            except ValueError as e:
                logger.error(e)
                logger.error('\n⚠️ Wrong page name! Please check EXCEL_PAGE_NAME ⚠️')
                raise ValueError(f"{e}")

            instances = []
            for index, row in wb.iterrows():
                instance = data_class.from_dataframe_row(row)
                instances.append(instance)

            return instances

    except (DecryptionError, InvalidKeyError, DecryptionError, ValueError) as e:
        logger.error(e)
        sys.exit()
