from multiprocessing import Value
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import uuid
from src.auth.models import HeightUnit, AccountCreationType

EMAIL_MAX_LEN = 99
PASSWORD_MIN_LEN = 6

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: uuid.UUID
    username: str
    first_name: str
    last_name: str
    is_verified: bool
    email: str
    password_hash: str = Field(exclude=True)
    role: str
    created_at: datetime
    birth_month : int | None
    birth_year : int | None
    height_raw: float | None
    height_unit: str | None
    age: int | None # auto-filled from model attributes
    full_name : str | None # ^

class UserCreate(BaseModel):
    username: str = Field(max_length=EMAIL_MAX_LEN)
    first_name: str = Field(max_length=99)
    last_name: str = Field(max_length=99)
    email: str = Field(max_length=99)
    password: str | None = Field(default=None, min_length=PASSWORD_MIN_LEN)
    birth_month: int | None = Field(default=None, ge=1, le=12)
    birth_year: int | None = Field(default=None, le=datetime.now().year)
    height_raw : float | None = Field(default=None, ge=0)
    height_unit : str | None # Strictly either "CENTIMETERS" or "INCHES", represented in SQLAlchemy as SQLEnum
    account_creation_type : str

    model_config = {
    "json_schema_extra": {
        "example": {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe123@co.com",
            "password": "testpass123",
            "birth_month" : 1,
            "birth_year" : 1999,
            "height_raw" : 187,
            "height_unit" : "CENTIMETERS",
            "account_creation_type" : "CUSTOM"
        }
    }}

    @field_validator('height_unit', mode='before')
    def validate_unit(cls, val: str) -> str | None:
        valid_fields = set(field.name for field in HeightUnit)
        if val and val not in valid_fields:
            raise ValueError("Improper metric, units must be either 'CENTIMETERS' or 'INCHES'")
        return val

class UserLogin(BaseModel):
    email: str = Field(max_length=EMAIL_MAX_LEN)
    password: str = Field(min_length=PASSWORD_MIN_LEN)

class UserLogout(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, max_length=24)
    first_name: str | None = Field(default=None, max_length=25)
    last_name: str | None = Field(default=None, max_length=25)
    email: str | None = Field(default=None, max_length=EMAIL_MAX_LEN)
    password: str | None = Field(default=None, min_length=PASSWORD_MIN_LEN)
    birth_month: int | None = Field(default=None, ge=1, le=12)
    birth_year: int | None = Field(default=None, ge=1900, le=datetime.now().year)
    height_raw : float | None = Field(default=None, ge=0)
    height_unit : str | None = None # Strictly either "CENTIMETERS" or "INCHES", represented in SQLAlchemy as SQLEnum

    @field_validator('height_unit', mode='before')
    def validate_unit(cls, val: str) -> str | None:
        valid_fields = set(field.name for field in HeightUnit)
        if val and val not in valid_fields:
            raise ValueError("Improper metric, units must be either 'CENTIMETERS' or 'INCHES'")
        return val

class ExchangeData(BaseModel):
    exchange_code: str