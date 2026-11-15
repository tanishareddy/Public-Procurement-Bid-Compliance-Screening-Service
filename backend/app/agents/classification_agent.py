import time
from typing import Dict, Any
from app.graph.state import AgentState
from app.schemas.bid_schemas import BidderCategory
from app.guardrails.input_guardrails import PromptGuardrail

class ClassificationAgent:
    """
    Agent 1: Bid Classification & Entity Extraction Agent.
    - Determines real bidder category based strictly on verified documentation.
    - Never infers a startup or MSE purely from free-text remarks.
    - Identifies missing or ambiguous information.
    - Scans for prompt injection attacks.
    """
    @staticmethod
    def execute(state: AgentState) -> AgentState:
        start_time = time.time()
        payload = state["bid_payload"]
        step_num = state["step_count"] + 1
        
        # 1. Guardrail Inspection on free text
        remarks = payload.get("additional_remarks", "")
        safe, reason = PromptGuardrail.inspect_text(remarks)
        if not safe:
            trace_entry = {
                "step_number": step_num,
                "agent_name": "ClassificationAgent",
                "step_type": "guardrail_violation",
                "action": "inspect_text",
                "action_input": {"remarks": remarks},
                "action_output": {"error": reason},
                "step_latency_ms": round((time.time() - start_time) * 1000, 2),
                "step_status": "blocked"
            }
            state["step_count"] = step_num
            state["trace_steps"].append(trace_entry)
            state["guardrail_triggered"] = True
            state["routing_recommendation"] = "reject-with-cited-condition"
            state["escalation_reason"] = f"Security Policy Violation: {reason}"
            state["screening_summary"] = "Bid submission rejected due to adversarial prompt injection."
            return state

        # 2. Strict Category Verification
        claimed_cat = payload.get("bidder_category", "unknown")
        dpiit_no = payload.get("dpiit_recognition_number")
        udyam_no = payload.get("udyam_registration_number")
        is_consortium = payload.get("is_consortium", False)
        country = payload.get("country_of_incorporation", "IN")
        docs = payload.get("supporting_documents", [])

        established = BidderCategory.UNKNOWN.value
        confidence = 0.5
        is_ambiguous = False

        if country.upper() != "IN":
            established = BidderCategory.FOREIGN.value
            confidence = 0.95
        elif is_consortium:
            established = BidderCategory.CONSORTIUM.value
            confidence = 0.95
        elif claimed_cat == BidderCategory.STARTUP.value:
            has_dpiit_doc = any(
                "dpiit" in (d.get("document_name", "") + " " + d.get("document_type", "")).lower() 
                for d in docs
            )
            if dpiit_no or has_dpiit_doc:
                established = BidderCategory.STARTUP.value
                confidence = 0.98
            else:
                is_ambiguous = True
                established = BidderCategory.UNKNOWN.value
                confidence = 0.3
        elif claimed_cat == BidderCategory.MSE.value:
            has_udyam_doc = any(
                "udyam" in (d.get("document_name", "") + " " + d.get("document_type", "")).lower()
                for d in docs
            )
            if udyam_no or has_udyam_doc:
                established = BidderCategory.MSE.value
                confidence = 0.98
            else:
                is_ambiguous = True
                established = BidderCategory.UNKNOWN.value
                confidence = 0.3
        else:
            established = BidderCategory.LARGE_ENTERPRISE.value
            confidence = 0.90

        # Extract qualification entities
        entities = {
            "annual_turnover_inr": payload.get("annual_turnover_inr", 0.0),
            "prior_experience_years": payload.get("prior_experience_years", 0),
            "emd_amount_inr": payload.get("emd_amount_inr", 0.0),
            "emd_paid": payload.get("emd_paid", False),
            "emd_exemption_claimed": payload.get("emd_exemption_claimed", False),
            "claimed_exemptions": payload.get("claimed_exemptions", []),
            "dpiit_number": dpiit_no,
            "udyam_number": udyam_no,
            "supporting_docs_count": len(docs)
        }

        trace_entry = {
            "step_number": step_num,
            "agent_name": "ClassificationAgent",
            "step_type": "entity_extraction",
            "action": "classify_bidder",
            "action_input": {"claimed_category": claimed_cat, "country": country},
            "action_output": {
                "established_category": established,
                "confidence": confidence,
                "is_ambiguous": is_ambiguous,
                "extracted_entities": entities
            },
            "step_latency_ms": round((time.time() - start_time) * 1000, 2),
            "step_status": "success",
            "prompt_tokens": 150,
            "completion_tokens": 60,
            "step_cost_usd": 0.00003
        }

        # Update state
        state["step_count"] = step_num
        state["trace_steps"].append(trace_entry)
        state["established_category"] = established
        state["category_confidence"] = confidence
        state["is_category_ambiguous"] = is_ambiguous
        state["qualification_entities"] = entities
        state["prompt_tokens"] += 150
        state["completion_tokens"] += 60
        state["total_tokens"] += 210
        state["estimated_cost_usd"] += 0.00003

        return state
