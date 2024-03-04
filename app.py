from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import os
import uuid
from PIL import Image
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Define the directory where you want to save the uploaded files
IMAGE_DIRECTORY = getenv("IMAGES_DIRECTORY", "uploads/images")

REQUIRED_DIRECTORIES = [IMAGE_DIRECTORY]

for d in REQUIRED_DIRECTORIES:
    print(f"checking if {d} exists...")
    try:
        os.makedirs(d, exist_ok=False)
        print(f"{d} created!")
    except OSError:
        print(f"{d} already exists!")

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
    


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
