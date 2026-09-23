from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import SessionLocal
from sqlalchemy.orm import Session
from app.models import Trace
import uuid
import time
from app.rag import generate_rag_answer

app = FastAPI(title="RAG Observability API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class TraceResponse(BaseModel):
    trace_id: str
    question: str
    answer: str
    llm_latency: float
    retrieval_latency: float
    embedding_latency: float
    vector_search_latency: float
    total_latency: float
    input_tokens: int
    output_tokens: int
    thought_tokens: int
    total_tokens: int

class TraceListResponse(BaseModel):
    trace_id: str
    question: str
    answer: str | None
    status: str
    error_stage: str | None
    retrieval_latency: float | None
    embedding_latency: float | None
    vector_search_latency: float | None
    llm_latency: float | None
    total_latency: float | None
    input_tokens: int | None
    output_tokens: int | None
    thought_tokens: int | None
    total_tokens: int | None

class MetricsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    average_latency: float | None
    average_retrieval_latency: float | None
    average_llm_latency: float | None
    total_tokens: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "LLM Observability API is running"}

    
@app.post("/ask", response_model=TraceResponse)
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    trace_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        result = generate_rag_answer(request.question)

        total_latency = time.perf_counter() - start_time

        trace = Trace(
            trace_id=trace_id,
            question=request.question,
            answer=result["answer"],
            model="gemini-3.6-flash",
            embedding_latency=result["embedding_latency"],
            vector_search_latency=result["vector_search_latency"],
            retrieval_latency=result["retrieval_latency"],
            llm_latency=result["latency"],
            total_latency=total_latency,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            thought_tokens=result["thought_tokens"],
            total_tokens=result["total_tokens"],
            status="success",
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        return TraceResponse(
            trace_id=trace_id,
            question=request.question,
            answer=result["answer"],
            embedding_latency=result["embedding_latency"],
            vector_search_latency=result["vector_search_latency"],
            retrieval_latency=result["retrieval_latency"],
            llm_latency=result["latency"],
            total_latency=total_latency,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            thought_tokens=result["thought_tokens"],
            total_tokens=result["total_tokens"],
        )

    except Exception as e:
        total_latency = time.perf_counter() - start_time

        error_message = str(e)
        # print("ASK ERROR:", error_message)

        # if error_message.startswith("embedding:"):
        #     error_stage = "embedding"

        if error_message.startswith("embedding:"):
            error_stage = "embedding"
        elif error_message.startswith("vector_search:"):
            error_stage = "vector_search"
        elif error_message.startswith("llm:"):
            error_stage = "llm"
        else:
            error_stage = "unknown"

        trace = Trace(
            trace_id=trace_id,
            question=request.question,
            model="gemini-3.6-flash",
            total_latency=total_latency,
            status="error",
            error_stage=error_stage,
            error=error_message,
        )

        db.add(trace)
        db.commit()

        raise HTTPException(
            status_code=503,
            detail="Request failed",
        )


@app.get("/traces", response_model=list[TraceListResponse])
def get_traces(db: Session = Depends(get_db)):
    traces = (db.query(Trace).order_by(Trace.timestamp.desc()).limit(100).all())
    return traces

@app.get("/traces/{trace_id}", response_model=TraceListResponse)
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    trace = db.query(Trace).filter(Trace.trace_id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    traces = db.query(Trace).all()

    total_requests = len(traces)

    successful_requests = sum(
        1 for trace in traces
        if trace.status == "success"
    )

    failed_requests = sum(
        1 for trace in traces
        if trace.status == "error"
    )

    error_rate = (
        failed_requests / total_requests
        if total_requests > 0
        else 0
    )

    latencies = [
        trace.total_latency
        for trace in traces
        if trace.total_latency is not None
    ]

    retrieval_latencies = [
        trace.retrieval_latency
        for trace in traces
        if trace.retrieval_latency is not None
    ]

    llm_latencies = [
        trace.llm_latency
        for trace in traces
        if trace.llm_latency is not None
    ]

    total_tokens = sum(
        trace.total_tokens or 0
        for trace in traces
    )

    return MetricsResponse(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        error_rate=error_rate,
        average_latency=(
            sum(latencies) / len(latencies)
            if latencies
            else None
        ),
        average_retrieval_latency=(
            sum(retrieval_latencies) / len(retrieval_latencies)
            if retrieval_latencies
            else None
        ),
        average_llm_latency=(
            sum(llm_latencies) / len(llm_latencies)
            if llm_latencies
            else None
        ),
        total_tokens=total_tokens,
    )