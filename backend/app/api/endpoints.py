import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.db_models import BidRunModel, AgentTraceStepModel, QuarantineRecordModel, ScreeningFeedbackModel, CorpusDocumentModel
from app.schemas.bid_schemas import (
    BidSubmissionRequest, BidRunSubmissionResponse, BidScreeningResult,
    QuarantineRecordResponse, FeedbackSubmissionRequest, FeedbackSummaryResponse, RunStatus
)
from app.services.ingestion_validator import IngestionValidator
from app.services.run_execution_service import run_screening_worker_task

router = APIRouter(prefix="/api/v1")

# F1, F2: Submit bid summary and validate boundary
@router.post("/bids", response_model=BidRunSubmissionResponse, status_code=202)
def submit_bid(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: dict,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Strict Ingestion Validation and Quarantine
    is_valid, validated_bid, errors = IngestionValidator.validate_and_quarantine(payload, client_ip, db)
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Malformed request rejected at ingestion boundary. Quarantined without starting agent run.",
                "validation_errors": errors
            }
        )

    # Valid payload -> Create run record
    run_id = str(uuid.uuid4())
    bid_run = BidRunModel(
        run_id=run_id,
        tender_id=validated_bid.tender_id,
        bidder_name=validated_bid.bidder_name,
        bidder_category_claimed=validated_bid.bidder_category.value,
        status=RunStatus.PENDING.value,
        raw_request_payload=payload
    )
    db.add(bid_run)
    db.commit()
    db.refresh(bid_run)

    # Dispatch asynchronous execution
    background_tasks.add_task(run_screening_worker_task, run_id, validated_bid.tender_id, payload)

    return BidRunSubmissionResponse(
        run_id=run_id,
        status=RunStatus.PENDING,
        message="Bid screening run accepted and queued for execution.",
        created_at=bid_run.created_at,
        poll_url=f"/api/v1/runs/{run_id}"
    )

# Run status & result endpoint
@router.get("/runs/{run_id}", response_model=BidScreeningResult)
def get_run_result(run_id: str, db: Session = Depends(get_db)):
    run = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Screening run '{run_id}' not found.")

    if run.status in [RunStatus.PENDING.value, RunStatus.PROCESSING.value]:
        raise HTTPException(
            status_code=202,
            detail={"status": run.status, "message": "Screening run is currently in progress."}
        )

    if run.status == RunStatus.FAILED.value:
        raise HTTPException(
            status_code=500,
            detail={"status": "failed", "error": run.error_message}
        )

    return BidScreeningResult(
        run_id=run.run_id,
        tender_id=run.tender_id,
        bidder_name=run.bidder_name,
        established_category=run.established_category or "unknown",
        confidence_score=run.category_confidence or 0.0,
        routing_recommendation=run.routing_recommendation or "seek-clarification",
        screening_summary=run.screening_summary or "",
        escalation_reason=run.escalation_reason,
        condition_findings=run.condition_findings or [],
        citations=run.citations or [],
        completed_at=run.completed_at or datetime.utcnow(),
        execution_time_seconds=run.execution_time_seconds or 0.0,
        prompt_version=run.prompt_version or "v2",
        total_tokens_used=run.total_tokens_used or 0,
        estimated_cost_usd=run.estimated_cost_usd or 0.0
    )

# Execution trace endpoint
@router.get("/runs/{run_id}/trace")
def get_run_trace(run_id: str, db: Session = Depends(get_db)):
    run = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")

    steps = (
        db.query(AgentTraceStepModel)
        .filter(AgentTraceStepModel.run_id == run_id)
        .order_by(AgentTraceStepModel.step_number.asc())
        .all()
    )

    return {
        "run_id": run_id,
        "tender_id": run.tender_id,
        "bidder_name": run.bidder_name,
        "status": run.status,
        "execution_time_seconds": run.execution_time_seconds,
        "total_tokens": run.total_tokens_used,
        "total_cost_usd": run.estimated_cost_usd,
        "steps_count": len(steps),
        "steps": [
            {
                "step_number": s.step_number,
                "agent_name": s.agent_name,
                "step_type": s.step_type,
                "action": s.action,
                "action_input": s.action_input,
                "action_output": s.action_output,
                "status": s.step_status,
                "latency_ms": s.step_latency_ms,
                "tokens": s.prompt_tokens + s.completion_tokens,
                "cost_usd": s.step_cost_usd,
                "timestamp": s.created_at.isoformat()
            }
            for s in steps
        ]
    }

# Feedback endpoints
@router.post("/feedback", status_code=201)
def submit_feedback(payload: FeedbackSubmissionRequest, db: Session = Depends(get_db)):
    run = db.query(BidRunModel).filter(BidRunModel.run_id == payload.run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Screening run not found.")

    feedback_record = ScreeningFeedbackModel(
        run_id=payload.run_id,
        satisfactory=payload.satisfactory,
        rating=payload.rating,
        reason=payload.reason,
        user_id=payload.user_id
    )
    db.add(feedback_record)
    db.commit()
    return {"message": "Feedback submitted successfully.", "run_id": payload.run_id}

@router.get("/feedback/summary", response_model=FeedbackSummaryResponse)
def get_feedback_summary(db: Session = Depends(get_db)):
    all_fb = db.query(ScreeningFeedbackModel).all()

    total = len(all_fb)
    if total == 0:
        return FeedbackSummaryResponse(
            total_feedback=0,
            satisfactory_count=0,
            unsatisfactory_count=0,
            satisfactory_percentage=0.0,
            average_rating=0.0,
            recent_comments=[]
        )

    sat_count = sum(1 for f in all_fb if f.satisfactory)
    unsat_count = total - sat_count
    avg_rating = round(sum(f.rating for f in all_fb) / total, 2)
    sat_pct = round((sat_count / total) * 100, 1)

    recent = [
        {"run_id": f.run_id, "rating": f.rating, "satisfactory": f.satisfactory, "reason": f.reason}
        for f in all_fb[-5:]
    ]

    return FeedbackSummaryResponse(
        total_feedback=total,
        satisfactory_count=sat_count,
        unsatisfactory_count=unsat_count,
        satisfactory_percentage=sat_pct,
        average_rating=avg_rating,
        recent_comments=recent
    )

# Corpus Management endpoints
@router.get("/corpus")
def get_corpus_documents():
    import json, os
    manifest_path = "data/corpus/processed/index_manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Corpus manifest not found. Run ingestion pipeline."}

@router.post("/corpus/refresh")
def refresh_corpus(background_tasks: BackgroundTasks):
    from app.ingestion.pipeline import CorpusIngestionPipeline
    pipeline = CorpusIngestionPipeline()
    summary = pipeline.process_and_index()
    return {"message": "Corpus indexing executed successfully.", "summary": summary}

# System metrics summary for UI Dashboard
@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    runs = db.query(BidRunModel).order_by(desc(BidRunModel.created_at)).limit(100).all()
    
    total_runs = len(runs)
    completed = sum(1 for r in runs if r.status == "completed")
    escalated = sum(1 for r in runs if r.routing_recommendation == "escalate-to-committee")
    clarification = sum(1 for r in runs if r.routing_recommendation == "seek-clarification")
    passed = sum(1 for r in runs if r.routing_recommendation == "pass-to-technical-evaluation")
    rejected = sum(1 for r in runs if r.routing_recommendation == "reject-with-cited-condition")

    recent_runs = [
        {
            "run_id": r.run_id,
            "bidder_name": r.bidder_name,
            "category": r.established_category or r.bidder_category_claimed,
            "routing": r.routing_recommendation,
            "status": r.status,
            "duration": r.execution_time_seconds,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in runs[:10]
    ]

    return {
        "total_runs": total_runs,
        "completed_runs": completed,
        "escalated_runs": escalated,
        "clarification_runs": clarification,
        "passed_runs": passed,
        "rejected_runs": rejected,
        "recent_activity": recent_runs
    }

# Quarantine inspect endpoint
@router.get("/quarantine")
def get_quarantined_requests(db: Session = Depends(get_db)):
    records = db.query(QuarantineRecordModel).order_by(desc(QuarantineRecordModel.quarantined_at)).limit(50).all()
    return [
        {
            "id": r.id,
            "tender_id": r.tender_id,
            "bidder_name": r.bidder_name,
            "validation_errors": r.validation_errors,
            "raw_payload": r.raw_payload,
            "client_ip": r.client_ip,
            "quarantined_at": r.quarantined_at.isoformat() if r.quarantined_at else None
        }
        for r in records
    ]
