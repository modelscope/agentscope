import os
import hashlib
import time
import zipfile
from pathlib import Path


class ZipCompressor:
    @staticmethod
    def compress(input_path, output_path):
        input_path = Path(input_path)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            if input_path.is_dir():
                for file in input_path.rglob('*'):
                    zip_file.write(file, file.relative_to(input_path))
            else:
                zip_file.write(input_path, input_path.name)

    @staticmethod
    def decompress(input_path, output_path):
        with zipfile.ZipFile(input_path, 'r') as zip_file:
            zip_file.extractall(path=output_path)

def get_hash(text):
    text += str(time.time())
    return hashlib.md5(text.encode('utf-8')).hexdigest()
