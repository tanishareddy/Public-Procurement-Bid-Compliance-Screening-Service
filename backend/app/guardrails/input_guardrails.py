import re
from typing import Tuple, Optional

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"override\s+(all\s+)?rules",
    r"bypass\s+compliance",
    r"automatically\s+qualify",
    r"qualify\s+this\s+bid",
    r"approve\s+this\s+bid",
    r"pass-to-technical-evaluation",
    r"delete\s+all",
    r"drop\s+table"
]

CANARY_PHRASE = "CONFIDENTIAL_COMPLIANCE_EVALUATION_DO_NOT_REVEAL"

class PromptGuardrail:
    @staticmethod
    def inspect_text(text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Scans input free-text fields for prompt injection, jailbreaking, or instruction smuggling.
        Returns (is_safe, violation_reason).
        """
        if not text:
            return True, None

        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return False, f"Adversarial instruction detected matching pattern: '{pattern}'"
        
        # Check for excessive delimiter abuse or pseudo system tags
        if "<system>" in text_lower or "</system>" in text_lower or "[instruction]" in text_lower:
            return False, "Detected prohibited prompt framing markup."

        return True, None

    @staticmethod
    def sanitize_context(raw_text: str) -> str:
        """
        Wraps untrusted input into clear data boundaries to prevent instruction poisoning.
        """
        cleaned = raw_text.replace("<system>", "").replace("</system>", "")
        return f"<bid_data>\n{cleaned.strip()}\n</bid_data>"
