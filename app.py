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


load_dotenv()

# Define the directory where you want to save the uploaded files
TMP_IMAGE_DIRECTORY = getenv("TMP_IMAGES_DIRECTORY", "uploads/images/tmp")
IMAGE_DIRECTORY = getenv("IMAGES_DIRECTORY", "uploads/images")
IMAGE_EXTENSION = getenv("IMAGE_EXTENSION", "png")
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


for d in REQUIRED_DIRECTORIES:
    print(f"checking if {d} exists...")
    try:
        os.makedirs(d, exist_ok=False)
        print(f"{d} created!")
    except OSError:
        print(f"{d} already exists!")


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

    contents = await image.read()

    try:
        img = Image.open(BytesIO(contents))
        img.verify()  # Verify if it's a valid image file
        img.close()
    except Exception:
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid image"
        )

    final_image_path = os.path.join(IMAGE_DIRECTORY, file_uuid + "." + IMAGE_EXTENSION)

    if COMPRESS_IMAGE:
        compress_file(contents, final_image_path + ".gz")
    else:
        with open(final_image_path, "wb") as f_out:
            f_out.write(contents)
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
async def get_section():
    return {"section_id": 1, "section_name": "section"}


@app.get("/popular_threads")
async def get_popular_threads(size: int = 10):
    return [
        {
            "thread_id": 1,
            "username": "123",
            "title": "1234",
            "section_id": "1234",
            "description": "1234",
            "image_uuid": None,
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
                media_type="image/" + IMAGE_EXTENSION,
            )

        path = os.path.join(IMAGE_DIRECTORY, image_uuid + "." + IMAGE_EXTENSION)
        if not os.path.exists(path):
            raise HTTPException(status_code=400, detail="uuid not found")

        return FileResponse(path, media_type="image/" + IMAGE_EXTENSION)
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
        return StreamingResponse(img_io, media_type="image/" + IMAGE_EXTENSION)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
