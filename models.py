from pydantic import BaseModel
from typing import Union


class Post(BaseModel):
    user_id: Union[int, None] = None
    section_id: int
    title: str
    content: Union[str, None] = None
    image_uuid: Union[str, None] = None
    parent_id: Union[int, None] = None
