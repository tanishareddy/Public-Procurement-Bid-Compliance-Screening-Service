from typing import Dict, Any, List
from app.schemas.bid_schemas import RoutingOutcome

class OutputGuardrail:
    """
    Enforces the Critical Legal Safety Rule:
    The AI system must NEVER issue a binding legal determination.
    All outputs are screening recommendations for the tender committee.
    """
    @staticmethod
    def validate_and_sanitize(result: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = result.get("routing_recommendation")
        
        # Verify recommendation is one of the legal routing outcomes
        valid_outcomes = [o.value for o in RoutingOutcome]
        if recommendation not in valid_outcomes:
            result["routing_recommendation"] = RoutingOutcome.ESCALATE_TO_COMMITTEE.value
            result["escalation_reason"] = f"Output guardrail caught unrecognized routing outcome: {recommendation}"
            
        # Ensure mandatory disclaimer
        legal_disclaimer = (
            "DISCLAIMER: This screening report is an automated preliminary compliance evaluation "
            "generated for the Tender Screening Committee. In compliance with public procurement rules, "
            "the system never unilaterally accepts or rejects a bid. Decision authority resides exclusively "
            "with the competent Tender Committee."
        )
        if "screening_summary" in result:
            result["screening_summary"] = f"{result['screening_summary']}\n\n{legal_disclaimer}"
        else:
            result["screening_summary"] = legal_disclaimer

        return result
