from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.responses import FileResponse, StreamingResponse
import os
import uuid
from PIL import Image
from os import getenv
from dotenv import load_dotenv
from models import Post
from database.DatabaseManager import DatabaseManager
from io import BytesIO
from Utils.Compression import compress_file, decompress_file, is_compressed
from init import (
    required_directories_init,
    check_save_support,
    check_save_all_support,
    get_best_conversion,
)


load_dotenv()

# Define the directory where you want to save the uploaded files
TMP_IMAGE_DIRECTORY = getenv("TMP_IMAGES_DIRECTORY", "uploads/images/tmp")
IMAGE_DIRECTORY = getenv("IMAGES_DIRECTORY", "uploads/images")
IMAGE_FORMAT = getenv("IMAGE_FORMAT", "webp").upper()
IMAGE_EXTENSION = getenv("IMAGE_EXTENSION", "webp")
COMPRESS_IMAGE = getenv("COMPRESS_IMAGE", "true").lower() in [
    "true",
    "1",
    "t",
    "y",
    "yes",
    "yeah",
    "yup",
    "certainly",
    "uh-huh",
]


DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./test.db")
REQUIRED_DIRECTORIES = [TMP_IMAGE_DIRECTORY, IMAGE_DIRECTORY]
SAVE_ALL = False
IMAGE_MODE = "P"


def initialization():
    required_directories_init(REQUIRED_DIRECTORIES=REQUIRED_DIRECTORIES)

    if not check_save_support(IMAGE_FORMAT):
        print(f"Image extension {IMAGE_FORMAT} does not support saving!")
        exit(1)
    else:
        print(f"Image extension {IMAGE_FORMAT} supports saving!")

    global SAVE_ALL
    SAVE_ALL = check_save_all_support(IMAGE_FORMAT)

    if SAVE_ALL:
        print(f"Image extension {IMAGE_FORMAT} supports saving all frames!")
    else:
        print(f"Image extension {IMAGE_FORMAT} does not support saving all frames!")

    global IMAGE_MODE
    IMAGE_MODE = get_best_conversion(IMAGE_FORMAT)

    if IMAGE_MODE:
        print(f"Image extension {IMAGE_FORMAT} supports {IMAGE_MODE} mode!")


db = DatabaseManager(DATABASE_URL)
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload/image")
async def upload_image(image: UploadFile = File(...)):
    # Create the directory if it doesn't exist
    os.makedirs(TMP_IMAGE_DIRECTORY, exist_ok=True)
    os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

    # Generate a unique UUID for the file
    file_uuid = str(uuid.uuid4())

    content = await image.read()

    try:
        img = Image.open(BytesIO(content))
        img.verify()  # Verify if it's a valid image file

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid image"
        )

    img = Image.open(BytesIO(content))

    final_image_path = os.path.join(IMAGE_DIRECTORY, file_uuid + "." + IMAGE_EXTENSION)

    converted_content = BytesIO()
    img = img.convert(IMAGE_MODE)

    try:
        if SAVE_ALL:
            print("saving all frames...")
            img.save(converted_content, format=IMAGE_FORMAT.upper(), save_all=True)
            print("saved!")
        else:
            print("saving...")
            img.save(converted_content, format=IMAGE_FORMAT.upper())
            print("saved!")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded image cannot be converted in {IMAGE_FORMAT}!",
        )

    converted_bytes = converted_content.getvalue()

    if COMPRESS_IMAGE:
        compress_file(converted_bytes, final_image_path + ".gz")
        img.close()
    else:
        with open(final_image_path, "wb") as f_out:
            f_out.write(converted_bytes)
        img.close()
    # Return a response indicating the UUID of the saved image
    return {"image_uuid": file_uuid}


@app.post("/newPost")
async def create_thread(post: Post):
    # TODO: check for image_uuid existence, section and parent
    id = db.create_thread(
        title=post.title,
        username=post.username,
        content=post.content,
        image_uuid=post.image_uuid,
        section_id=post.section_id,
        parent_id=post.parent_id,
    )
    return {"post_id": id}


@app.get("/getThreads")
async def get_threads_by_section(
    section_id: int = None, page: int = 0, size: int = 50, ascending: bool = False
):
    try:
        threads = db.get_threads(
            section_id=section_id, page=page, size=size, ascending=ascending
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response_obj = {}

    # create a json response
    t = []
    for thread in threads:
        t.append(
            {
                "id": thread.id,
                "title": thread.title,
                "username": thread.username,
                "content": thread.content,
                "image_uuid": thread.image_uuid,
                "section_id": thread.section_id,
                "parent_id": thread.parent_id,
            }
        )

    response_obj["threads"] = t
    response_obj["size"] = len(threads)
    response_obj["page"] = page
    response_obj["page_amount"] = db.get_post_max_pages(
        section_id=section_id, size=size
    )
    response_obj["ascending_order"] = ascending

    return response_obj


@app.get("/getPost")
async def get_post_by_id(post_id: int):
    thread = db.get_thread_by_id(post_id)
    if not thread:
        return HTTPException(
            status_code=400, detail=f"no post fount with id = {post_id}"
        )
    response = {
        "id": thread.id,
        "title": thread.title,
        "username": thread.username,
        "content": thread.content,
        "image_uuid": thread.image_uuid,
        "section_id": thread.section_id,
        "parent_id": thread.parent_id,
        "is_thread": thread.parent_id is None,
    }
    comments = db.get_comments_by_thread_id(post_id)
    response["comments"] = []
    for comment in comments:
        response["comments"].append(
            {
                "id": comment.id,
                "title": comment.title,
                "username": comment.username,
                "content": comment.content,
                "image_uuid": comment.image_uuid,
                "section_id": comment.section_id,
                "parent_id": comment.parent_id,
            }
        )

    return response


@app.get("/getSections")
async def get_sections():
    sections = db.get_all_sections()
    sections_resp = []

    for section in sections:
        sections_resp.append(
            {"section_id": section.id, "section_name": section.section_name}
        )

    return {"sections": sections_resp}


@app.get("/motd")
async def get_motd():
    return {"motd": db.get_random_motd().motd}


@app.get("/getSection")
async def get_section(section_id: int):
    section = db.get_section_by_id(section_id)
    # return {"section_id": 1, "section_name": "section"}
    return {"section_id": section.id, "section_name": section.section_name}


@app.get("/popular_threads")
async def get_popular_threads(size: int = 10):
    post = db.get_random_post()
    print(post.__dict__)
    return [
        {
            "thread_id": post.id,
            "title": post.title,
            "username": post.username,
            "content": post.content,
            "image_uuid": post.image_uuid,
            "section_id": post.section_id,
            "parent_id": post.parent_id,
        }
    ]


@app.get("/retrieve/image/{image_uuid}")
async def retrieve_image(image_uuid: str):
    print(image_uuid)
    if not COMPRESS_IMAGE:
        if image_uuid.endswith(IMAGE_EXTENSION) and os.path.exists(
            os.path.join(IMAGE_DIRECTORY, image_uuid)
        ):
            return FileResponse(
                os.path.join(IMAGE_DIRECTORY, image_uuid),
                media_type="image/" + IMAGE_FORMAT.lower(),
            )

        path = os.path.join(IMAGE_DIRECTORY, image_uuid + "." + IMAGE_EXTENSION)
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="uuid not found")

        return FileResponse(path, media_type="image/" + IMAGE_FORMAT.lower())
    else:
        if image_uuid.endswith(IMAGE_EXTENSION) and os.path.exists(
            os.path.join(IMAGE_DIRECTORY, image_uuid + ".gz")
        ):
            img_io = BytesIO(
                decompress_file(
                    os.path.join(IMAGE_DIRECTORY, image_uuid + ".gz"),
                    save_decompressed_file=False,
                )
            )
        else:
            path = os.path.join(
                IMAGE_DIRECTORY, image_uuid + "." + IMAGE_EXTENSION + ".gz"
            )

            if not os.path.exists(path):
                raise HTTPException(status_code=400, detail="uuid not found")

            img_io = BytesIO(
                decompress_file(
                    os.path.join(
                        IMAGE_DIRECTORY, image_uuid + "." + IMAGE_EXTENSION + ".gz"
                    ),
                    save_decompressed_file=False,
                )
            )

        img_io.seek(0)
        return StreamingResponse(img_io, media_type="image/" + IMAGE_FORMAT.lower())


if __name__ == "__main__":
    initialization()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
