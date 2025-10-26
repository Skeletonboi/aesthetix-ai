from pydantic import BaseModel
from uuid import UUID


class TagBase(BaseModel):
    tid: UUID
    tag_name: str
    tag_color: str

class TagCreate(BaseModel):
    tag_name: str
    tag_color: str