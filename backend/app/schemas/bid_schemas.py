from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from datetime import datetime

class BidderCategory(str, Enum):
    LARGE_ENTERPRISE = "large_enterprise"
    MSE = "mse"
    STARTUP = "startup"
    CONSORTIUM = "consortium"
    FOREIGN = "foreign"
    UNKNOWN = "unknown"

class ClaimedExemptionType(str, Enum):
    PRIOR_TURNOVER = "prior_turnover"
    PRIOR_EXPERIENCE = "prior_experience"
    EMD_EXEMPTION = "emd_exemption"
    TENDER_FEE = "tender_fee"

class DocumentReference(BaseModel):
    document_name: str = Field(..., min_length=2, max_length=255)
    document_type: str = Field(..., min_length=2, max_length=100)
    reference_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[str] = None
    issuing_authority: Optional[str] = None

class BidSubmissionRequest(BaseModel):
    tender_id: str = Field(..., min_length=3, max_length=100, description="Unique identifier of the published tender")
    bidder_name: str = Field(..., min_length=2, max_length=255, description="Legal registered name of the bidder")
    bidder_category: BidderCategory = Field(..., description="Self-claimed category of the bidder")
    
    # Financial qualifications
    annual_turnover_inr: float = Field(..., ge=0.0, description="Average annual turnover in INR for specified years")
    prior_experience_years: int = Field(..., ge=0, le=100, description="Completed years of relevant experience")
    
    # EMD (Earnest Money Deposit)
    emd_amount_inr: float = Field(0.0, ge=0.0, description="Submitted EMD amount in INR")
    emd_paid: bool = Field(False, description="Whether EMD has been deposited")
    emd_exemption_claimed: bool = Field(False, description="Whether bidder claims exemption from EMD")
    
    # Special registrations / verifications
    dpiit_recognition_number: Optional[str] = Field(None, max_length=100, description="DPIIT recognition number for Startups")
    udyam_registration_number: Optional[str] = Field(None, max_length=100, description="Udyam Registration Number for MSEs")
    is_consortium: bool = Field(False, description="Whether the bid is submitted by a consortium/JV")
    lead_partner_name: Optional[str] = Field(None, max_length=255)
    country_of_incorporation: str = Field("IN", min_length=2, max_length=3, description="ISO country code")
    
    # Claims and attachments
    claimed_exemptions: List[ClaimedExemptionType] = Field(default_factory=list)
    supporting_documents: List[DocumentReference] = Field(default_factory=list)
    additional_remarks: Optional[str] = Field(None, max_length=2000)

    # Cross-field validations
    @model_validator(mode="after")
    def validate_cross_field_rules(self) -> "BidSubmissionRequest":
        # 1. Startup claiming exemption must provide DPIIT recognition number or document
        if self.bidder_category == BidderCategory.STARTUP:
            has_dpiit_doc = any(
                "dpiit" in (d.document_name + " " + d.document_type).lower() 
                or "startup" in (d.document_name + " " + d.document_type).lower()
                for d in self.supporting_documents
            )
            if not self.dpiit_recognition_number and not has_dpiit_doc:
                raise ValueError("Bidders claiming Startup category must provide a DPIIT recognition number or supporting certificate in supporting_documents.")

        # 2. MSE claiming exemption must provide Udyam registration
        if self.bidder_category == BidderCategory.MSE:
            has_udyam_doc = any(
                "udyam" in (d.document_name + " " + d.document_type).lower() 
                or "msme" in (d.document_name + " " + d.document_type).lower()
                for d in self.supporting_documents
            )
            if not self.udyam_registration_number and not has_udyam_doc:
                raise ValueError("Bidders claiming MSE category must provide an Udyam registration number or certificate in supporting_documents.")

        # 3. EMD validation: either paid or exemption claimed with valid reason
        if not self.emd_paid and not self.emd_exemption_claimed and self.emd_amount_inr == 0:
            raise ValueError("Bid must specify either emd_paid=True with valid amount, or emd_exemption_claimed=True.")

        # 4. Consortium must specify lead partner
        if self.is_consortium and not self.lead_partner_name:
            raise ValueError("Consortium bids must declare a lead_partner_name.")

        # 5. Foreign bidder check
        if self.country_of_incorporation.upper() != "IN" and self.bidder_category != BidderCategory.FOREIGN:
            raise ValueError(f"Bidder with foreign country code '{self.country_of_incorporation}' must be classified as 'foreign'.")

        return self

class RunStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class RoutingOutcome(str, Enum):
    PASS_TO_TECHNICAL = "pass-to-technical-evaluation"
    SEEK_CLARIFICATION = "seek-clarification"
    REJECT_WITH_CITED_CONDITION = "reject-with-cited-condition"
    ESCALATE_TO_COMMITTEE = "escalate-to-committee"

class ConditionComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    EXEMPTED_BY_POLICY = "exempted_by_policy"
    REQUIRES_CLARIFICATION = "requires_clarification"
    CONFLICT_REQUIRES_COMMITTEE = "conflict_requires_committee"

class Citation(BaseModel):
    document_id: str
    document_title: str
    clause_number: Optional[str] = None
    page_number: Optional[int] = None
    quoted_text: str
    issuing_authority: Optional[str] = None

class ConditionFinding(BaseModel):
    condition_name: str
    category: str # "turnover", "experience", "emd", "legal"
    tender_clause: Optional[str] = None
    status: ConditionComplianceStatus
    details: str
    tender_citation: Optional[Citation] = None
    policy_citation: Optional[Citation] = None
    statutory_override_detected: bool = False

class BidScreeningResult(BaseModel):
    run_id: str
    tender_id: str
    bidder_name: str
    established_category: BidderCategory
    confidence_score: float
    routing_recommendation: RoutingOutcome
    screening_summary: str
    escalation_reason: Optional[str] = None
    condition_findings: List[ConditionFinding] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    completed_at: datetime
    execution_time_seconds: float
    prompt_version: str
    total_tokens_used: int
    estimated_cost_usd: float

class BidRunSubmissionResponse(BaseModel):
    run_id: str
    status: RunStatus
    message: str
    created_at: datetime
    poll_url: str

class QuarantineRecordResponse(BaseModel):
    id: str
    tender_id: Optional[str] = None
    bidder_name: Optional[str] = None
    raw_payload: Dict[str, Any]
    validation_errors: List[str]
    quarantined_at: datetime
    client_ip: Optional[str] = None

class FeedbackSubmissionRequest(BaseModel):
    run_id: str
    satisfactory: bool
    rating: int = Field(..., ge=1, le=5)
    reason: str = Field(..., min_length=3, max_length=1000)
    user_id: Optional[str] = None

class FeedbackSummaryResponse(BaseModel):
    total_feedback: int
    satisfactory_count: int
    unsatisfactory_count: int
    satisfactory_percentage: float
    average_rating: float
    recent_comments: List[Dict[str, Any]]
