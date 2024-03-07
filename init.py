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
    img = Image.new("RGB", (1, 1))  # Create a dummy image
    buffer = BytesIO()
    buffer.seek(0)
    img.save(buffer, format=image_format.upper())  # Save to BytesIO
    print("sas")
    return True


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


def get_best_conversion(image_format: str) -> str:
    buffer = BytesIO()
    try:
        img = Image.new("P", (1, 1))  # Create a dummy image
        img = img.convert("P")
        img.save(buffer, format=image_format.upper())  # Save to BytesIO
        return "P"
    except OSError:
        pass

    try:
        img = Image.new("RGBA", (1, 1))  # Create a dummy image
        img = img.convert("RGBA")
        img.save(buffer, format=image_format.upper())  # Save to BytesIO
        return "RGBA"
    except OSError:
        pass

    try:
        img = Image.new("RGB", (1, 1))  # Create a dummy image
        img = img.convert("RGB")
        img.save(buffer, format=image_format.upper())  # Save to BytesIO
        return "RGB"
    except OSError:
        pass

    try:
        img = Image.new("L", (1, 1))  # Create a dummy image
        img = img.convert("L")
        img.save(buffer, format=image_format.upper())  # Save to BytesIO
        return "L"
    except OSError:
        pass

    raise OSError("No valid conversion found!")
