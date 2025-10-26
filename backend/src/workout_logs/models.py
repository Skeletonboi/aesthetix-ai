from sqlalchemy import Column, Date, DateTime, Integer, String, Float, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from src.db.base_model import BaseModel
from uuid import uuid4

class WorkoutLog(BaseModel):
    __tablename__ = "workout_logs"

    __table_args__ = (
        UniqueConstraint("user_uid", "exercise_eid", "reps", "weight", "date_performed", "created_at", name="log_fingerprint"),
    )

    wid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_uid = Column(UUID(as_uuid=True), ForeignKey("user_accounts.uid"), nullable=False)
    exercise_eid = Column(UUID(as_uuid=True), ForeignKey("exercises.eid"), nullable=False)
    
    reps = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    date_performed = Column(Date(), server_default=func.current_date())
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    
    
    user = relationship("User", back_populates="logs", lazy="selectin")
    exercise = relationship("Exercise", back_populates="logs", lazy="joined")

    def __repr__(self):
        return f"{self.reps} x {self.weight} of {self.exercise.exercise_slug}"
    