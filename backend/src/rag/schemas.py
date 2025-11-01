from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class RAGRequest(BaseModel):
    msg: str

class RAGInternalRequest(RAGRequest):
    user_uid: UUID

class RAGSingleResponse(BaseModel):
    ai_msg: str

class ResearchResultFull(BaseModel):
    result_id: UUID
    user_uid: UUID | None = None
    user_query: str
    created_at: datetime
    
    research_queries: list[str] | None = None
    embedding_queries: list[str] | None = None
    
    transcript_chunks: list[dict] | None = None
    txtbk_chunks: list[dict] | None = None
    research_papers: list[dict] | None = None
    
    llm_chunk_response: list[str] | None = None
    llm_final_response: str | None = None

    model_config = ConfigDict(from_attributes=True)

class ResearchResultHistoryItem(BaseModel):
    result_id: UUID
    user_query: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)