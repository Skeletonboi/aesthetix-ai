from src.db.base_model import BaseModel
from sqlalchemy import Column, String, UUID, Table, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4


exercise_tags = Table(
    "exercise_tags",
    BaseModel.metadata,
    Column("eid", UUID(as_uuid=True), ForeignKey("exercises.eid"), primary_key=True, server_default="sa.text."),
    Column("tid", UUID(as_uuid=True), ForeignKey("tags.tid"), primary_key=True),
)


# workout_tags = Table(
#     "workout_tags",
#     BaseModel.metadata,
#     Column("workout_id", UUID(as_uuid=True), ForeignKey("workout_logs.wid"), primary_key=True),
#     Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.tid"), primary_key=True),
# )


class Tag(BaseModel):
    __tablename__ = "tags"

    tid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    tag_name = Column(String, nullable=False, unique=True)
    tag_color = Column(String, nullable=False, default="#808080")

    exercises = relationship("Exercise", secondary=exercise_tags, back_populates="tags")
    # workout_logs = relationship("WorkoutLog", secondary=workout_tags, back_populates="tags")


# SQLModel syntax
# class ExerciseTag(BaseModel):
#     __tablename__ = "exercise_tags"

#     exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.eid"), primary_key=True)
#     tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.tid"), primary_key=True)


# class WorkoutTag(BaseModel):
#     __tablename__ = "workout_tags"

#     workout_id = Column(UUID(as_uuid=True), ForeignKey("workout_logs.wid"), primary_key=True)
#     tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.tid"), primary_key=True)