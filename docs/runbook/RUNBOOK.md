# Operations Runbook — Public Procurement Bid Compliance Screening Service

## Incident 1: Asynchronous Task Queue / Redis Broker Outage

### Symptoms:
- Client receives `status: pending` indefinitely when polling `/api/v1/runs/{run_id}`.
- Celery / background worker logs show `redis.exceptions.ConnectionError: Connection refused`.

### Confirmation:
```powershell
docker compose ps redis
curl -i http://localhost:8000/api/v1/health
```

### Recovery:
1. Verify Redis container health:
   ```powershell
   docker compose restart redis
   ```
2. Verify Redis responsiveness using redis-cli:
   ```powershell
   docker compose exec redis redis-cli ping
   ```
3. Restart failed worker tasks:
   ```powershell
   docker compose restart agent-worker
   ```
4. If running locally without Docker, fallback to direct execution mode by setting `ASYNC_MODE=direct` in `.env`.

---

## Incident 2: LLM Provider Circuit Breaker Tripped

### Symptoms:
- Client receives `escalate-to-committee` with message stating provider unavailability.
- Prometheus counter `agent_step_total{status="circuit_breaker_open"}` spikes.

### Confirmation:
Inspect recent agent trace steps:
```powershell
curl http://localhost:8000/api/v1/runs/<run_id>/trace
```
Search for `step_status: "circuit_breaker_open"`.

### Recovery:
1. Check external provider rate limits or billing quotas.
2. The circuit breaker resets automatically after `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` (default: 30s).
3. Switch immediately to local stub provider without application downtime by updating `.env`:
   ```ini
   LLM_PROVIDER=stub
   ```
4. Graceful degradation path guarantees no hallucinated or unverified answers are ever returned.
