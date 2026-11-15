import time
from datetime import datetime
from typing import Dict, Any
from app.graph.compliance_graph import execute_screening_pipeline
from app.database.session import SessionLocal
from app.models.db_models import BidRunModel, AgentTraceStepModel
from app.schemas.bid_schemas import RunStatus

def run_screening_worker_task(run_id: str, tender_id: str, payload: Dict[str, Any]):
    """
    Executes the screening pipeline, records all trace steps,
    tokens, costs, and findings, and updates the BidRun in the database.
    """
    start_time = time.time()
    db = SessionLocal()
    
    try:
        # Mark as processing
        run_record = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
        if run_record:
            run_record.status = RunStatus.PROCESSING.value
            db.commit()

        # Execute LangGraph pipeline
        final_state = execute_screening_pipeline(run_id, tender_id, payload)
        execution_duration = round(time.time() - start_time, 3)

        # Persist trace steps
        for step in final_state.get("trace_steps", []):
            trace_entry = AgentTraceStepModel(
                run_id=run_id,
                step_number=step.get("step_number", 1),
                agent_name=step.get("agent_name", "UnknownAgent"),
                step_type=step.get("step_type", "action"),
                action=step.get("action"),
                action_input=step.get("action_input"),
                action_output=step.get("action_output"),
                step_status=step.get("step_status", "success"),
                step_latency_ms=step.get("step_latency_ms", 0.0),
                prompt_tokens=step.get("prompt_tokens", 0),
                completion_tokens=step.get("completion_tokens", 0),
                step_cost_usd=step.get("step_cost_usd", 0.0)
            )
            db.add(trace_entry)

        # Update BidRun record
        run_record = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
        if run_record:
            run_record.status = RunStatus.COMPLETED.value
            run_record.established_category = final_state.get("established_category")
            run_record.category_confidence = final_state.get("category_confidence")
            run_record.qualification_entities = final_state.get("qualification_entities")
            run_record.routing_recommendation = final_state.get("routing_recommendation")
            run_record.condition_findings = final_state.get("condition_findings")
            
            citations = final_state.get("tender_citations", []) + final_state.get("statutory_citations", [])
            run_record.citations = citations
            run_record.escalation_reason = final_state.get("escalation_reason")
            run_record.screening_summary = final_state.get("screening_summary")
            run_record.total_tokens_used = final_state.get("total_tokens", 0)
            run_record.prompt_tokens = final_state.get("prompt_tokens", 0)
            run_record.completion_tokens = final_state.get("completion_tokens", 0)
            run_record.estimated_cost_usd = final_state.get("estimated_cost_usd", 0.0)
            run_record.execution_time_seconds = execution_duration
            run_record.completed_at = datetime.utcnow()
            
        db.commit()

    except Exception as e:
        db.rollback()
        run_record = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
        if run_record:
            run_record.status = RunStatus.FAILED.value
            run_record.error_message = str(e)
            run_record.completed_at = datetime.utcnow()
            db.commit()
        raise e
    finally:
        db.close()
