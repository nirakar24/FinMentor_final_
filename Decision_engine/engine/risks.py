from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from .models import NormalizedInput, RuleTrigger, RiskItem
from .config import DEFAULTS

logger = logging.getLogger(__name__)


def _severity_to_multiplier(severity: str) -> float:
    """
    Convert severity to numeric multiplier for weighted scoring.
    
    Multipliers:
    - low: 1.0
    - medium: 2.0
    - high: 3.0
    - none: 0.0
    """
    return {"none": 0.0, "low": 1.0, "medium": 2.0, "high": 3.0}.get(severity, 1.0)


def _band_to_score(band: str) -> int:
    """Legacy: Convert severity band to simple score."""
    return {"none": 0, "low": 33, "medium": 66, "high": 100}.get(band, 0)


def _max_severity(a: str, b: str) -> str:
    """Return the higher severity between two."""
    order = ["none", "low", "medium", "high"]
    return a if order.index(a) >= order.index(b) else b


def _calculate_weighted_score(contributors: List[Dict]) -> Tuple[float, float, str]:
    """
    Calculate weighted risk score from contributors.
    
    Formula: risk_score = sum(weight × severity_multiplier)
    
    Args:
        contributors: List of contributor dicts with rule_id, severity, weight
        
    Returns:
        Tuple of (weighted_score, max_possible_score, overall_severity)
    """
    if not contributors:
        return 0.0, 0.0, "none"
    
    weighted_score = 0.0
    max_possible_score = 0.0
    max_severity = "none"
    
    for contrib in contributors:
        weight = contrib.get("weight", 1.0)
        severity = contrib.get("severity", "low")
        
        # Calculate weighted contribution
        severity_mult = _severity_to_multiplier(severity)
        weighted_score += weight * severity_mult
        
        # Max possible is if this rule was "high" severity
        max_possible_score += weight * 3.0  # 3.0 is high severity multiplier
        
        # Track overall max severity
        max_severity = _max_severity(max_severity, severity)
    
    return weighted_score, max_possible_score, max_severity


def build_risks(data: NormalizedInput, rules: List[RuleTrigger]) -> List[RiskItem]:
    # Map contributors by dimension
    dims: Dict[str, Dict] = {
        "deficit": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "overspend": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "savings": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "volatility": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "stability": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "discretionary": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
        "category_outlier": {"sev": "none", "reasons": [], "refs": [], "contributors": []},
    }

    dim_map = {
        # Bucket 1: Budget Stability → deficit, overspend, savings
        "R-DEFICIT-01": "deficit",
        "R-FCAST-DEF-01": "deficit",
        "R-CONSEC-DEF-01": "deficit",
        "R-OVRSPEND-01": "overspend",
        "R-WEEKLY-SPIKE-01": "overspend",
        "R-SAVE-LOW-01": "savings",
        "R-EMERG-FUND-01": "savings",
        "R-SAVE-DEPLETE-01": "savings",
        "R-RENT-HIGH-01": "overspend",
        # Bucket 2: Volatility & Risk → volatility, stability
        "R-VOL-INC-01": "volatility",
        "R-INCOME-DROP-01": "volatility",
        "R-CASHFLOW-VAR-01": "volatility",
        "R-STAB-LOW-01": "stability",
        "R-LARGE-TXN-01": "stability",
        "R-ZERO-INC-DAYS-01": "stability",
        # Bucket 3: Category-Based → category_outlier, discretionary
        "R-DISC-HIGH-01": "discretionary",
        "R-HSD-01": "discretionary",
        "R-CAT-DRIFT-01": "category_outlier",
        "R-TOP-CAT-HEAVY-01": "category_outlier",
        "R-FOOD-HIGH-01": "category_outlier",
        "R-TRANSPORT-HIGH-01": "category_outlier",
        "R-UTILITIES-SPIKE-01": "category_outlier",
        "R-CASH-SPIKE-01": "category_outlier",
        "R-LOAN-EMI-HIGH-01": "category_outlier",
        # Bucket 4: Forecast-Driven → deficit, savings (or new dimension)
        "R-FCAST-SURPLUS-01": "savings",  # Positive signal
        "R-BUFFER-WARN-01": "savings",
        "R-FCAST-CONF-LOW-01": "stability",
        "R-FCAST-DEF-LARGE-01": "deficit",
    }

    for r in rules:
        if not r.triggered:
            continue
        dim = dim_map.get(r.rule_id)
        if not dim:
            continue
        dims[dim]["sev"] = _max_severity(dims[dim]["sev"], r.severity or "low")
        if r.reason:
            dims[dim]["reasons"].append(r.reason)
        dims[dim]["refs"].extend(r.data_refs)
        
        # Include weight from rule trigger
        weight = getattr(r, 'weight', 1.0)  # Default to 1.0 if not present
        dims[dim]["contributors"].append({
            "rule_id": r.rule_id, 
            "severity": r.severity, 
            "weight": weight
        })

    # Aggregate into RiskItem list with weighted scoring
    risks: List[RiskItem] = []
    for dim, info in dims.items():
        contributors = info["contributors"]
        if not contributors:
            continue
        
        # Calculate weighted score
        weighted_score, max_possible, overall_severity = _calculate_weighted_score(contributors)
        
        # Normalize to 0-100 scale for consistency
        normalized_score = (weighted_score / max_possible * 100) if max_possible > 0 else 0
        
        summary = f"{dim.capitalize()} risk: {overall_severity}"
        
        logger.info(f"Risk {dim}: weighted_score={weighted_score:.2f}, max_possible={max_possible:.2f}, "
                   f"normalized={normalized_score:.1f}, severity={overall_severity}")
        
        risks.append(
            RiskItem(
                id=f"RK-{dim.upper()}",
                dimension=dim,  # type: ignore
                score=round(normalized_score, 1),  # Normalized 0-100 score
                severity=overall_severity,  # type: ignore
                summary=summary,
                reasons=info["reasons"],
                data_refs=list(dict.fromkeys(info["refs"])),
                contributors=contributors,
                weighted_score=round(weighted_score, 2),
                max_possible_score=round(max_possible, 2)
            )
        )

    return risks
