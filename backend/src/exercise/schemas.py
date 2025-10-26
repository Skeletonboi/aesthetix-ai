from pydantic import BaseModel
from typing import Optional, ClassVar, Set, List
from src.tags.schemas import TagBase

class ExerciseBase(BaseModel):
    exercise_slug: str
    exercise_name: str
    meta_data: Optional[dict] = None

class ExerciseCreate(ExerciseBase):
    tag_slugs: List[str]

class ExerciseUpdate(ExerciseCreate):
    new_slug: str

class ExerciseResponse(ExerciseBase):
    tags: List[TagBase]