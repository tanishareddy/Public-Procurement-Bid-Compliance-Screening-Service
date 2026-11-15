from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Run identifiers
    run_id: str
    tender_id: str
    bid_payload: Dict[str, Any]
    
    # Execution & telemetry
    step_count: int
    tool_calls_count: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    trace_steps: List[Dict[str, Any]]
    
    # Agent 1 outputs: Bidder Classification & Qualification Entities
    established_category: str
    category_confidence: float
    is_category_ambiguous: bool
    qualification_entities: Dict[str, Any]
    
    # Agent 2 outputs: Compliance Research Findings
    retrieved_passages: List[Dict[str, Any]]
    condition_findings: List[Dict[str, Any]]
    potential_statutory_conflict: bool
    statutory_citations: List[Dict[str, Any]]
    tender_citations: List[Dict[str, Any]]
    
    # Agent 3 outputs: Verification & Routing
    verification_passed: bool
    verification_errors: List[str]
    routing_recommendation: str
    escalation_reason: Optional[str]
    screening_summary: str
    
    # Guardrail / Error flags
    guardrail_triggered: bool
    error: Optional[str]
