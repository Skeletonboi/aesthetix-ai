from multiprocessing import Value
from sqlalchemy import Integer, Column, String, Boolean, DateTime, Float, func, extract, case, Enum as SQLEnum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, VARCHAR
from sqlalchemy.ext.hybrid import hybrid_property
from src.db.base_model import BaseModel
from uuid import uuid4
from datetime import datetime
from enum import Enum

class HeightUnit(Enum):
    CENTIMETERS = "cm" 
    INCHES = "in"

class User(BaseModel):
    __tablename__ = "user_accounts"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    username = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())
    birth_month = Column(Integer, nullable=True)
    birth_year = Column(Integer, nullable=True)
    height_raw = Column(Float, nullable=True)
    height_unit = Column(SQLEnum(HeightUnit), nullable=True)

    role = Column(VARCHAR, nullable=False, server_default="user")

    logs = relationship("WorkoutLog", back_populates="user", lazy="selectin")
    search_results = relationship("ResearchResult", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"User {self.username}"
    
    def __init__(self, **kwargs):
        col_names = set(col.name for col in self.__table__.columns)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in col_names}

        super().__init__(**filtered_kwargs)
    
    @property
    def height_cm(self):
        if not self.height_unit or not self.height_raw:
            return None
        if self.height_unit == HeightUnit.CENTIMETERS:
            return self.height_raw
        else:
            return self.height_raw * 2.54

    @property
    def height_in(self):
        if not self.height_unit or not self.height_raw:
            return None
        if self.height_unit == HeightUnit.INCHES:
            return self.height_raw
        else:
            return self.height_raw / 2.54

    @validates("birth_month", "birth_year")
    def validate_birth_month_year(self, key, val):
        if key == 'birth_month':
            if val < 1 or val > 12:
                raise ValueError("Invalid birth_month")
        elif key == 'birth_year':
            if val < 1900 or val > datetime.now().year:
                raise ValueError("Invalid birth year")
        return val

    @hybrid_property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.last_name]))
    
    @full_name.expression
    def full_name(cls):
        return func.concat(func.coalesce(cls.first_name, ''), " ", func.coalesce(cls.last_name, ''))

    @hybrid_property
    def age(self):
        if not self.birth_year or not self.birth_month:
            return None
        curr_age = datetime.now().year - self.birth_year
        if self.birth_month > datetime.now().month:
            curr_age -= 1
        return curr_age
    
    @age.expression
    def age(cls):
        curr_year = extract('year', func.current_date())
        curr_month = extract('month', func.current_date())

        return case(
            (cls.birth_month.is_(None), None),
            (cls.birth_year.is_(None), None),
            (cls.birth_month > curr_month, curr_year - cls.birth_year - 1),
            else_ = curr_year - cls.birth_year
        )