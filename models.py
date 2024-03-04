from fastapi import FastAPI
from pydantic import BaseModel

class Thread (BaseModel):
    username: str
    section_id: int
    title: str
    content: str = None
    image_uuid: str = None
    parent_id: int = None


    
