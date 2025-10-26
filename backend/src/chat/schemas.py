from pydantic import BaseModel
import uuid

class ChatRequest(BaseModel):
    msg: str

class ChatInternalRequest(ChatRequest):
    user_uid: uuid.UUID

class ChatSingleResponse(BaseModel):
    ai_msg: str