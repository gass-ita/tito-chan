from pydantic import BaseModel


class Post(BaseModel):
    username: str = "Anonymous"
    section_id: int
    title: str
    content: str = None
    image_uuid: str = None
    parent_id: int = None
