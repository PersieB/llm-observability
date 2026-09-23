import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base


class Trace(Base):
    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, index=True)

    trace_id = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)

    model = Column(String, nullable=False)

    llm_latency = Column(Float, nullable=True)
    total_latency = Column(Float, nullable=True)
    retrieval_latency = Column(Float, nullable=True)
    embedding_latency = Column(Float, nullable=True)
    vector_search_latency = Column(Float, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    thought_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    status = Column(String, nullable=False)

    error = Column(Text, nullable=True)
    error_stage = Column(String, nullable=True)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String, nullable=False)

    text = Column(Text, nullable=False)

    embedding = Column(Vector(3072), nullable=False)