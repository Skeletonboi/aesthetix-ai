from src.db.base_model import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from src.tags.models import exercise_tags

from uuid import uuid4

class Exercise(BaseModel):
    __tablename__ = "exercises"
    
    eid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    exercise_slug = Column(String, nullable=False, unique=True)
    exercise_name = Column(String, nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    logs = relationship("WorkoutLog", back_populates="exercise", lazy="selectin")
    tags = relationship("Tag", secondary=exercise_tags, back_populates="exercises", lazy="selectin")

    def __repr__(self):
        return f"Exercise {self.exercise_slug}"