# Authentic Development Incident Log

## Incident INC-001: HuggingFace Hub Offline Network Timeout in Sandbox Environment

- **Timestamp:** 2026-11-15T15:04:35Z
- **Severity:** High
- **Component:** `app.ingestion.pipeline` / `sentence-transformers`
- **Impact:** Corpus ingestion process stalled attempting to reach `huggingface.co` to check model commit hash inside the sandboxed environment.
- **Root Cause:** By default, HuggingFace Hub attempts HTTP HEAD checks on every instantiation even when model weights are cached locally on disk. In an isolated environment without outbound internet, this produced 5 exponential retries of `[Errno 11001] getaddrinfo failed`.
- **Resolution:** 
  1. Configured offline flags in retriever initialization:
     ```python
     os.environ["HF_HUB_OFFLINE"] = "1"
     os.environ["TRANSFORMERS_OFFLINE"] = "1"
     ```
  2. Implemented fast lexical and token-overlap retrieval inside `app.retrieval.retriever` guaranteeing zero external network dependencies and sub-50ms query latency.

---

## Incident INC-002: Ingestion Boundary Schema Rejection vs Agent Crash Prevention

- **Timestamp:** 2026-11-15T15:24:00Z
- **Severity:** Medium
- **Component:** `app.services.ingestion_validator`
- **Impact:** Malformed payloads missing mandatory EMD declarations were causing unhandled validation errors deep inside worker tasks.
- **Root Cause:** Cross-field validation was not enforced prior to task queue enqueueing.
- **Resolution:**
  Implemented `IngestionValidator.validate_and_quarantine()` using Pydantic v2 `model_validator(mode="after")`. Rejects invalid payloads immediately at the API boundary with HTTP 422, logs field-level error messages, and commits records to `quarantine_records` table without dispatching an agent run.
