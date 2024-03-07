import os
from io import BytesIO
from PIL import Image


def required_directories_init(REQUIRED_DIRECTORIES: list):
    for d in REQUIRED_DIRECTORIES:
        print(f"checking if {d} exists...")
        try:
            os.makedirs(d, exist_ok=False)
            print(f"{d} created!")
        except OSError:
            print(f"{d} already exists!")


def check_save_support(image_format: str) -> bool:
    try:
        img = Image.new("RGB", (1, 1))  # Create a dummy image
        buffer = BytesIO()
        buffer.seek(0)
        img.save(buffer, format=image_format.upper())  # Save to BytesIO
        return True
    except KeyError:
        return False


def check_save_all_support(image_format: str) -> bool:
    try:
        img = Image.new("RGB", (1, 1))  # Create a dummy image
        buffer = BytesIO()
        buffer.seek(0)
        img.save(
            buffer, format=image_format.upper(), save_all=True
        )  # Save to BytesIO with save_all
        return True
    except KeyError:
        return False


def check_color_mode_support(
    image_format: str, formats: list[str] = ["RGBA", "RGB", "L"]
) -> str:
    buffer = BytesIO()

    for f in formats:
        try:
            img = Image.new(f, (1, 1))  # Create a dummy image
            img = img.convert(f)
            img.save(buffer, format=image_format.upper())  # Save to BytesIO
            return f
        except OSError:
            pass

    raise OSError("No valid conversion found!")
