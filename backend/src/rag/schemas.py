from pydantic import BaseModel
import uuid

class RAGRequest(BaseModel):
    msg: str

class RAGInternalRequest(RAGRequest):
    user_uid: uuid.UUID

class RAGSingleResponse(BaseModel):
    ai_msg: str