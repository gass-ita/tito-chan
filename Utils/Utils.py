from io import BytesIO
from typing import Union
import gzip
import shutil


def compress_bytes(data: bytes) -> bytes:
    with BytesIO() as f_in:
        f_in.write(data)
        f_in.seek(0)
        with BytesIO() as f_out:
            with gzip.open(f_out, "wb") as f:
                shutil.copyfileobj(f_in, f)
            return f_out.getvalue()


def decompress_bytes(data: bytes) -> bytes:
    with BytesIO(data) as f_in:
        with BytesIO() as f_out:
            with gzip.open(f_in, "rb") as f:
                shutil.copyfileobj(f, f_out)
            return f_out.getvalue()


def compress_file(
    file: Union[str, bytes], out_file: str = None, save_decompressed_file: bool = True
) -> bytes:
    if isinstance(file, str):
        with open(file, "rb") as f_in:
            data = f_in.read()
    else:
        data = file

    compressed_data = compress_bytes(data)

    if not out_file:
        if isinstance(file, str):
            out_file = file + ".gz"
        else:
            return compressed_data
    if save_decompressed_file:
        with open(out_file, "wb") as f_out:
            f_out.write(compressed_data)

    return compressed_data


def decompress_file(
    file: Union[str, bytes], out_file: str = None, save_decompressed_file: bool = True
) -> bytes:
    if isinstance(file, str):
        with open(file, "rb") as f_in:
            data = f_in.read()
    else:
        data = file

    decompressed_data = decompress_bytes(data)
    if not out_file:
        if isinstance(file, str):
            if file.endswith(".gz"):
                out_file = file[:-3]
            else:
                out_file = file + ".unarchived"
        else:
            return decompressed_data

    if save_decompressed_file:
        with open(out_file, "wb") as f_out:
            f_out.write(decompressed_data)

    return decompressed_data
