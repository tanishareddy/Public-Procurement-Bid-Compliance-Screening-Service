import time
from locust import HttpUser, task, between

class BidScreeningLoadTestUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def test_health(self):
        self.client.get("/api/v1/health")

    @task(2)
    def test_dashboard_metrics(self):
        self.client.get("/api/v1/dashboard/summary")

    @task(1)
    def test_startup_screening_run(self):
        payload = {
            "tender_id": "NICSI/PROC/2023/IT-INFRA-8921",
            "bidder_name": "Benchmark Startup Pvt Ltd",
            "bidder_category": "startup",
            "annual_turnover_inr": 15000000.0,
            "prior_experience_years": 1,
            "emd_amount_inr": 0.0,
            "emd_paid": False,
            "emd_exemption_claimed": True,
            "dpiit_recognition_number": "DPIIT-BENCH-9900",
            "supporting_documents": [
                {
                    "document_name": "DPIIT Certificate",
                    "document_type": "startup"
                }
            ]
        }
        with self.client.post("/api/v1/bids", json=payload, catch_response=True) as response:
            if response.status_code == 202:
                run_id = response.json().get("run_id")
                # Poll run status
                self.client.get(f"/api/v1/runs/{run_id}")
                response.success()
            else:
                response.failure(f"Failed with status: {response.status_code}")
