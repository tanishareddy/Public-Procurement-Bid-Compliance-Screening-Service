import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

class BidRunModel(Base):
    __tablename__ = "bid_runs"

    run_id = Column(String(64), primary_key=True, default=generate_uuid)
    tender_id = Column(String(100), nullable=False, index=True)
    bidder_name = Column(String(255), nullable=False)
    bidder_category_claimed = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="pending", index=True)
    
    # Payload & Parsed input
    raw_request_payload = Column(JSON, nullable=False)
    
    # Classification & Entity Results
    established_category = Column(String(50), nullable=True)
    category_confidence = Column(Float, nullable=True)
    qualification_entities = Column(JSON, nullable=True)
    
    # Compliance findings & Routing
    routing_recommendation = Column(String(50), nullable=True)
    condition_findings = Column(JSON, nullable=True)
    citations = Column(JSON, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    screening_summary = Column(Text, nullable=True)
    
    # LLMOps & Execution metadata
    prompt_version = Column(String(20), nullable=True, default="v2")
    llm_provider = Column(String(50), nullable=True)
    total_tokens_used = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    execution_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    trace_steps = relationship("AgentTraceStepModel", back_populates="run", cascade="all, delete-orphan")
    feedback = relationship("ScreeningFeedbackModel", back_populates="run", uselist=False)

class AgentTraceStepModel(Base):
    __tablename__ = "agent_trace_steps"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("bid_runs.run_id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    agent_name = Column(String(100), nullable=False)
    step_type = Column(String(50), nullable=False) # e.g. "thought", "tool_call", "tool_result", "verification"
    action = Column(String(100), nullable=True) # tool name
    action_input = Column(JSON, nullable=True)
    action_output = Column(JSON, nullable=True)
    step_status = Column(String(30), default="success") # success, error, retry
    step_latency_ms = Column(Float, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    step_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("BidRunModel", back_populates="trace_steps")

class QuarantineRecordModel(Base):
    __tablename__ = "quarantine_records"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    tender_id = Column(String(100), nullable=True)
    bidder_name = Column(String(255), nullable=True)
    raw_payload = Column(JSON, nullable=False)
    validation_errors = Column(JSON, nullable=False)
    client_ip = Column(String(50), nullable=True)
    quarantined_at = Column(DateTime, default=datetime.utcnow, index=True)

class ScreeningFeedbackModel(Base):
    __tablename__ = "screening_feedback"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("bid_runs.run_id"), nullable=False, unique=True)
    satisfactory = Column(Boolean, nullable=False)
    rating = Column(Integer, nullable=False) # 1 to 5
    reason = Column(Text, nullable=False)
    user_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("BidRunModel", back_populates="feedback")

class CorpusDocumentModel(Base):
    __tablename__ = "corpus_documents"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    document_name = Column(String(255), nullable=False, unique=True)
    document_type = Column(String(50), nullable=False) # tender, gfr, policy_order
    issuing_authority = Column(String(255), nullable=False)
    document_date = Column(String(50), nullable=True)
    source_url = Column(String(500), nullable=True)
    sha256_checksum = Column(String(64), nullable=False)
    total_pages = Column(Integer, default=1)
    total_chunks = Column(Integer, default=0)
    index_version = Column(String(50), default="1.0.0")
    raw_file_path = Column(String(500), nullable=False)
    processed_file_path = Column(String(500), nullable=False)
    indexed_at = Column(DateTime, default=datetime.utcnow)
