import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import init_db

client = TestClient(app)

def setup_module():
    asyncio.run(init_db())

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_malformed_request_rejection_and_quarantine():
    # Submit invalid request missing mandatory EMD declaration
    invalid_payload = {
        "tender_id": "NICSI/PROC/2023/IT-INFRA-8921",
        "bidder_name": "Incomplete Bidder Inc",
        "bidder_category": "large_enterprise",
        "annual_turnover_inr": 60000000.0,
        "prior_experience_years": 4,
        "emd_amount_inr": 0.0,
        "emd_paid": False,
        "emd_exemption_claimed": False # Violation: neither paid nor exemption claimed
    }
    response = client.post("/api/v1/bids", json=invalid_payload)
    assert response.status_code == 422
    data = response.json()
    assert "validation_errors" in data["detail"]

    # Verify record was stored in quarantine
    q_res = client.get("/api/v1/quarantine")
    assert q_res.status_code == 200
    quarantine_list = q_res.json()
    assert len(quarantine_list) > 0
    assert any(q["bidder_name"] == "Incomplete Bidder Inc" for q in quarantine_list)

def test_startup_relaxation_conflict_escalation():
    # Section 4.1 critical scenario
    startup_payload = {
        "tender_id": "NICSI/PROC/2023/IT-INFRA-8921",
        "bidder_name": "AeroTech Innovations Pvt Ltd",
        "bidder_category": "startup",
        "annual_turnover_inr": 12000000.0, # Below 5 Crores tender threshold
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
    submit_res = client.post("/api/v1/bids", json=startup_payload)
    assert submit_res.status_code == 202
    run_id = submit_res.json()["run_id"]

    # In TestClient, BackgroundTasks run synchronously before post() returns!
    result_res = client.get(f"/api/v1/runs/{run_id}")
    assert result_res.status_code == 200
    result_data = result_res.json()

    # Assert Section 4.1 requirements
    assert result_data["routing_recommendation"] == "escalate-to-committee"
    assert "STATUTORY CONFLICT DETECTED" in result_data["escalation_reason"]
    assert len(result_data["citations"]) >= 2
    cited_docs = [c["document_id"] for c in result_data["citations"]]
    assert any("Tender" in doc or "NICSI" in doc for doc in cited_docs)
    assert any("Startup" in doc or "DoE" in doc or "GFR" in doc for doc in cited_docs)
