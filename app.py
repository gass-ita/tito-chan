from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import os
import uuid
from PIL import Image
from os import getenv
from dotenv import load_dotenv
from models import Thread
from database import DatabaseManager

load_dotenv()

# Define the directory where you want to save the uploaded files
IMAGE_DIRECTORY = getenv("IMAGES_DIRECTORY", "uploads/images")
DATABASE_URL = getenv("DATABASE_URL", "sqlite:///./test.db")
REQUIRED_DIRECTORIES = [IMAGE_DIRECTORY]

for d in REQUIRED_DIRECTORIES:
    print(f"checking if {d} exists...")
    try:
        os.makedirs(d, exist_ok=False)
        print(f"{d} created!")
    except OSError:
        print(f"{d} already exists!")


db:DatabaseManager = DatabaseManager(DATABASE_URL)
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    # Create the directory if it doesn't exist
    os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

    # Generate a unique UUID for the file
    file_uuid = str(uuid.uuid4())

    # Determine the file path to save the uploaded file
    file_path = os.path.join(IMAGE_DIRECTORY, file_uuid)

    # Write the contents of the uploaded file to the specified file path
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)

    # Check if the uploaded file is an image
    try:
        img = Image.open(file_path)
        img.verify()  # Verify if it's a valid image file
        img.close()
    except Exception as e:
        os.remove(file_path)  # Delete the file if it's not a valid image
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid image"
        )

    # TODO: Compress the image

    # Return a response indicating the UUID of the saved image
    return {"image_uuid": file_uuid}

@app.post("/newThread")
async def create_thread(thread: Thread):
    id = db.create_thread(thread.title, thread.username, thread.content, thread.image_uuid, thread.section_id, thread.parent_id)
    return {"post_id": id}

@app.get("/getThreads?section_id={section_id}&page={page}&size={size}")
async def get_threads_by_section(section_id: int, page: int, size: int):
    threads = db.get_threads(section_id, page, size)
    
    #create a json response
    response = []
    for thread in threads:
        response.append({
            "id": thread.id,
            "title": thread.title,
            "username": thread.username,
            "content": thread.content,
            "image_uuid": thread.image_uuid,
            "section_id": thread.section_id,
            "parent_id": thread.parent_id
        })

    response.append({"page": page})
    response.append({"size": len(response)})

    return response

@app.get("/getThread?thread_id={thread_id}")
async def get_thread_by_id(thread_id: int):
    thread = db.get_thread_by_id(thread_id)
    response = {
        "id": thread.id,
        "title": thread.title,
        "username": thread.username,
        "content": thread.content,
        "image_uuid": thread.image_uuid,
        "section_id": thread.section_id,
        "parent_id": thread.parent_id

    }
    comments = db.get_comments_by_thread_id(thread_id)
    response["comments"] = []
    for comment in comments:
        response["comments"].append({
            "id": comment.id,
            "title": comment.title,
            "username": comment.username,
            "content": comment.content,
            "image_uuid": comment.image_uuid,
            "section_id": comment.section_id,
            "parent_id": comment.parent_id
        })

    return response









if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
