from typing import Tuple, Dict, Any, List
import pydantic
from app.schemas.bid_schemas import BidSubmissionRequest
from app.models.db_models import QuarantineRecordModel
from sqlalchemy.orm import Session

class IngestionValidator:
    """
    Enforces strict schema, type, range, categorical and cross-field validation
    at the boundary before any agent starts execution.
    Quarantines rejected payloads.
    """
    @staticmethod
    def validate_and_quarantine(
        payload: Dict[str, Any],
        client_ip: str,
        db: Session
    ) -> Tuple[bool, Any, List[str]]:
        try:
            validated_bid = BidSubmissionRequest.model_validate(payload)
            return True, validated_bid, []
        except pydantic.ValidationError as e:
            errors = []
            for err in e.errors():
                loc = " -> ".join([str(l) for l in err.get("loc", [])])
                msg = err.get("msg", "")
                errors.append(f"{loc}: {msg}")
            
            # Record into quarantine table
            quarantine_entry = QuarantineRecordModel(
                tender_id=str(payload.get("tender_id")) if payload.get("tender_id") else None,
                bidder_name=str(payload.get("bidder_name")) if payload.get("bidder_name") else None,
                raw_payload=payload,
                validation_errors=errors,
                client_ip=client_ip
            )
            db.add(quarantine_entry)
            db.commit()
            db.refresh(quarantine_entry)
            
            return False, None, errors
