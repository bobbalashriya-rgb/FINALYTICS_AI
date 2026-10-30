import enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from api.models import Operator

class EvaluationStatus(str, enum.Enum):
    PASS = "Pass"
    FAIL = "Fail"
    UNAVAILABLE = "Unavailable"

class PrincipleEvaluation(BaseModel):
    principle_name: str
    required_threshold: float
    actual_value: Optional[float]
    status: EvaluationStatus
    explanation: Optional[str] = None

class PrincipleEvaluationReport(BaseModel):
    evaluations: List[PrincipleEvaluation]
    passed_count: int
    total_count: int
    summary_text: str

def evaluate_principles(metrics: Dict[str, Optional[float]], principles: List[Any]) -> PrincipleEvaluationReport:
    """
    Evaluates a set of financial metrics against configured investment principles.
    Metrics parameter is expected to be a dictionary representation of CalculatedMetrics.
    """
    evaluations = []
    passed_count = 0
    total_count = len(principles)

    for p in principles:
        p_metric = getattr(p, 'metric', None) or (p.get('metric') if isinstance(p, dict) else None)
        p_name = getattr(p, 'name', None) or (p.get('name') if isinstance(p, dict) else 'Principle')
        p_threshold = float(getattr(p, 'threshold', 0) if not isinstance(p, dict) else p.get('threshold', 0))
        p_operator = getattr(p, 'operator', '>') if not isinstance(p, dict) else p.get('operator', '>')

        actual_value = metrics.get(p_metric)
        
        # Missing Data Rule: Never treat as zero, never fail, explicitly flag as UNAVAILABLE
        if actual_value is None:
            evaluations.append(PrincipleEvaluation(
                principle_name=p_name,
                required_threshold=p_threshold,
                actual_value=None,
                status=EvaluationStatus.UNAVAILABLE,
                explanation=f"The required financial metric '{p_metric}' is currently unavailable for this company."
            ))
            continue

        # Mathematical Evaluation Rule
        is_pass = False
        if p_operator in (Operator.GREATER_THAN, ">"):
            is_pass = actual_value > p_threshold
        elif p_operator in (Operator.LESS_THAN, "<"):
            is_pass = actual_value < p_threshold
        elif p_operator in (Operator.GREATER_THAN_OR_EQUAL, ">="):
            is_pass = actual_value >= p_threshold
        elif p_operator in (Operator.LESS_THAN_OR_EQUAL, "<="):
            is_pass = actual_value <= p_threshold

        status = EvaluationStatus.PASS if is_pass else EvaluationStatus.FAIL
        if is_pass:
            passed_count += 1

        evaluations.append(PrincipleEvaluation(
            principle_name=p_name,
            required_threshold=p_threshold,
            actual_value=actual_value,
            status=status,
            explanation=None
        ))

    # Strict compliance: Calculate count, add absolute disclaimer
    summary_text = (
        f"{passed_count} out of {total_count} principles passed. "
        "Disclaimer: This score represents only the evaluation of user-configured rules against available data. "
        "It is strictly not a buy signal, a sell signal, or a guaranteed investment recommendation."
    )

    return PrincipleEvaluationReport(
        evaluations=evaluations,
        passed_count=passed_count,
        total_count=total_count,
        summary_text=summary_text
    )

