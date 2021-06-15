import logging
import os
import stat
import sys
from typing import Optional

from subprocess import Popen, STDOUT


LOGGER = logging.getLogger(__name__)


class PdfAltoWrapper:
    def __init__(self, binary_path: str):
        self.binary_path = binary_path

    def ensure_excutable(self):
        st = os.stat(self.binary_path)
        os.chmod(self.binary_path, st.st_mode | stat.S_IEXEC)

    def get_command(
        self,
        pdf_path: str,
        output_path: str,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ):
        command = [
            self.binary_path,
            '-noImageInline',
            '-fullFontName',
            '-noLineNumbers'
        ]
        if first_page:
            command.extend(['-f', str(first_page)])
        if last_page:
            command.extend(['-l', str(last_page)])
        command.extend([
            pdf_path,
            output_path
        ])
        return command

    def convert_pdf_to_pdfalto_xml(self,  *args, **kwargs):
        command = self.get_command(*args, **kwargs)
        LOGGER.info('command: %s', command)
        LOGGER.info('command str: %s', ' '.join(command))
        with Popen(command, stdout=sys.stderr, stderr=STDOUT) as _:
            pass
