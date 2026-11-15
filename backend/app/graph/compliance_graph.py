import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.agents.classification_agent import ClassificationAgent
from app.agents.compliance_agent import ComplianceResearchAgent
from app.agents.verification_component import VerificationAndRoutingComponent
from app.config import settings

def build_compliance_graph():
    workflow = StateGraph(AgentState)

    # Add 3 distinct agent nodes
    workflow.add_node("classification_agent", ClassificationAgent.execute)
    workflow.add_node("compliance_agent", ComplianceResearchAgent.execute)
    workflow.add_node("verification_component", VerificationAndRoutingComponent.execute)

    # Define execution flow
    workflow.set_entry_point("classification_agent")
    
    # Conditional hand-off from classification
    def route_after_classification(state: AgentState):
        if state.get("guardrail_triggered", False):
            return END
        return "compliance_agent"

    workflow.add_conditional_edges(
        "classification_agent",
        route_after_classification,
        {
            "compliance_agent": "compliance_agent",
            END: END
        }
    )

    workflow.add_edge("compliance_agent", "verification_component")
    workflow.add_edge("verification_component", END)

    return workflow.compile()

# Global compiled graph instance
compliance_graph = build_compliance_graph()

def execute_screening_pipeline(run_id: str, tender_id: str, raw_payload: Dict[str, Any]) -> AgentState:
    initial_state: AgentState = {
        "run_id": run_id,
        "tender_id": tender_id,
        "bid_payload": raw_payload,
        "step_count": 0,
        "tool_calls_count": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "estimated_cost_usd": 0.0,
        "trace_steps": [],
        "established_category": "unknown",
        "category_confidence": 0.0,
        "is_category_ambiguous": False,
        "qualification_entities": {},
        "retrieved_passages": [],
        "condition_findings": [],
        "potential_statutory_conflict": False,
        "statutory_citations": [],
        "tender_citations": [],
        "verification_passed": False,
        "verification_errors": [],
        "routing_recommendation": "seek-clarification",
        "escalation_reason": None,
        "screening_summary": "",
        "guardrail_triggered": False,
        "error": None
    }
    
    # Execute through LangGraph
    final_state = compliance_graph.invoke(initial_state)
    return final_state
