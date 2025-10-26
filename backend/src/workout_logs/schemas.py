from pydantic import BaseModel, field_validator
from datetime import date, datetime
from src.exercise.schemas import ExerciseBase
from typing import List, ClassVar, Set
from uuid import UUID


class WorkoutLogBase(BaseModel):
    reps: float
    weight: float
    date_performed: date
    created_at: datetime | None = None
    
    class Config:
        from_attributes = True

class WorkoutLogCreate(WorkoutLogBase):
    exercise_slug: str

class WorkoutLogResponse(WorkoutLogBase):
    wid : UUID
    user_uid : UUID
    exercise: ExerciseBase

    @field_validator('exercise', mode='before')
    @classmethod
    def validate_exercise(cls, v):
        # Manual serialization for non-FastAPI route usage (because FastAPI does some magical coercion for nested models)
        if hasattr(v, '__table__'):
            return {
                'exercise_name' : v.exercise_name,
                'exercise_slug' : v.exercise_slug,
                'meta_data' : v.meta_data
            }
        
    
# Schema for updating is same as creation but without updated_at field
class WorkoutLogUpdate(BaseModel):
    exercise_slug: str
    reps: float
    weight: float
    date_performed: date
    
    class Config:
        from_attributes = True