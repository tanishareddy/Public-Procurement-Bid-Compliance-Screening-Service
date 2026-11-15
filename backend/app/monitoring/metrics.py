from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Metrics
AGENT_RUN_TOTAL = Counter("agent_runs_total", "Total screening runs submitted", ["status", "routing_outcome"])
AGENT_STEP_TOTAL = Counter("agent_steps_total", "Total agent reasoning and tool steps", ["agent_name", "status"])
AGENT_RUN_LATENCY = Histogram("agent_run_latency_seconds", "End-to-end execution latency per run")
TOOL_CALL_TOTAL = Counter("tool_calls_total", "Total tool calls made by agents", ["tool_name"])
TOKEN_USAGE_TOTAL = Counter("token_usage_total", "Token usage across runs", ["type"])

def get_prometheus_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
