from app.main import app
from app.database.session import init_db
from app.services.ingestion_validator import IngestionValidator
from app.services.run_execution_service import run_screening_worker_task
from app.database.session import SessionLocal
from app.models.db_models import BidRunModel, QuarantineRecordModel, AgentTraceStepModel
from app.schemas.bid_schemas import RunStatus
import uuid

def run_tests():
    print("[1/4] Initializing Database...")
    init_db()
    db = SessionLocal()

    try:
        # Test 1: Ingestion Boundary Validation & Quarantine (F2)
        print("[2/4] Testing Ingestion Boundary Validation & Quarantine...")
        invalid_payload = {
            "tender_id": "NICSI/PROC/2023/IT-INFRA-8921",
            "bidder_name": "Incomplete Bidder Inc",
            "bidder_category": "large_enterprise",
            "annual_turnover_inr": 60000000.0,
            "prior_experience_years": 4,
            "emd_amount_inr": 0.0,
            "emd_paid": False,
            "emd_exemption_claimed": False
        }
        is_valid, _, errors = IngestionValidator.validate_and_quarantine(invalid_payload, "127.0.0.1", db)
        assert not is_valid, "Expected validation to fail!"
        assert len(errors) > 0
        print("  -> Rejected successfully with validation errors:", errors[0])

        quarantined = db.query(QuarantineRecordModel).filter(QuarantineRecordModel.bidder_name == "Incomplete Bidder Inc").first()
        assert quarantined is not None, "Quarantine record not persisted in database!"
        print(f"  -> Quarantine verified! Stored ID: {quarantined.id}")

        # Test 2: Critical Section 4.1 Startup Relaxation Conflict Escalation
        print("[3/4] Testing Section 4.1 Startup Relaxation Conflict Escalation...")
        startup_payload = {
            "tender_id": "NICSI/PROC/2023/IT-INFRA-8921",
            "bidder_name": "AeroTech Innovations Pvt Ltd",
            "bidder_category": "startup",
            "annual_turnover_inr": 12000000.0, # 1.2 Crores (below 5 Crores tender condition)
            "prior_experience_years": 1,
            "emd_amount_inr": 0.0,
            "emd_paid": False,
            "emd_exemption_claimed": True,
            "dpiit_recognition_number": "DPIIT-2023-STARTUP-7890",
            "supporting_documents": [
                {
                    "document_name": "DPIIT Certificate of Recognition",
                    "document_type": "DPIIT Startup Certificate",
                    "reference_number": "DPIIT-2023-STARTUP-7890"
                }
            ]
        }
        is_valid, validated_bid, _ = IngestionValidator.validate_and_quarantine(startup_payload, "127.0.0.1", db)
        assert is_valid, "Valid startup payload failed ingestion validation!"

        run_id = str(uuid.uuid4())
        bid_run = BidRunModel(
            run_id=run_id,
            tender_id=validated_bid.tender_id,
            bidder_name=validated_bid.bidder_name,
            bidder_category_claimed=validated_bid.bidder_category.value,
            status=RunStatus.PENDING.value,
            raw_request_payload=startup_payload
        )
        db.add(bid_run)
        db.commit()

        # Run worker task synchronously
        run_screening_worker_task(run_id, validated_bid.tender_id, startup_payload)

        # Verify completed result
        run_result = db.query(BidRunModel).filter(BidRunModel.run_id == run_id).first()
        assert run_result.status == "completed"
        print("  -> Worker Execution Completed Successfully!")
        print("     Routing Recommendation:", run_result.routing_recommendation)
        print("     Established Category:", run_result.established_category)
        print("     Citations Count:", len(run_result.citations))
        print("     Summary:", run_result.screening_summary[:120], "...")

        assert run_result.routing_recommendation == "escalate-to-committee", (
            f"Expected escalate-to-committee, got {run_result.routing_recommendation}"
        )
        assert "STATUTORY CONFLICT DETECTED" in run_result.escalation_reason
        assert len(run_result.citations) >= 2

        # Test 3: Verify Detailed Trace Steps
        print("[4/4] Verifying Agent Execution Trace Steps...")
        trace_steps = db.query(AgentTraceStepModel).filter(AgentTraceStepModel.run_id == run_id).order_by(AgentTraceStepModel.step_number.asc()).all()
        assert len(trace_steps) >= 3, f"Expected at least 3 trace steps, got {len(trace_steps)}"
        for s in trace_steps:
            print(f"     Step {s.step_number} [{s.agent_name}]: action='{s.action}', latency={s.step_latency_ms}ms, cost=${s.step_cost_usd}")

        print("\n=========================================")
        print("ALL END-TO-END VERIFICATION TESTS PASSED COMPREHENSIVELY!")
        print("=========================================\n")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
