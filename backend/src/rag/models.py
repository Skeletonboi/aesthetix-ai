from sqlalchemy import Column, DateTime, String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from uuid import uuid4

from src.db.base_model import BaseModel

class ResearchResult():
    __tablename__ = "research_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_uid = Column(UUID(as_uuid=True), ForeignKey("user_accounts.uid"), nullable=True, index=True)
    user_query = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.current_timestamp())

    research_queries = Column(JSONB, nullable=True)
    embedding_queries = Column(JSONB, nullable=True)

    transcript_chunks = Column(JSONB, nullable=True)
    txtbk_chunks = Column(JSONB, nullable=True)
    research_papers = Column(JSONB, nullable=True)

    llm_chunk_response = Column(JSONB, nullable=True)
    llm_final_response = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="search_results")

    def __repr__(self):
        return (f"<ResearchResult(result_id={self.result_id}, "
                f"user_uid={self.user_uid}, "
                f"user_query='{self.user_query}', "
                f"created_at={self.created_at})>")