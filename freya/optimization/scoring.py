"""freya/optimization/scoring.py

OptimizationScoringEngine — evaluates the tradeoffs for a set of
OptimizationOpportunities and produces a single OptimizationEvaluation.

Scoring factors:
  economics impact     — cost delta weighted by confidence
  workflow quality     — quality_delta penalised heavily for negative values
  governance risk      — presence of approval-requiring opps raises risk tier
  execution latency    — time savings/costs normalised to hours
  cognitive reduction  — extra credit for reducing cognitive spend
  delegation reduction — extra credit for simplifying delegation chains

Net value score ∈ [-1, 1]:
  +1  = clear slam-dunk optimisation
   0  = neutral
  -1  = harmful (should be blocked)
"""
from __future__ import annotations

from freya.optimization.models import (
    OptimizationEvaluation,
    OptimizationOpportunity,
)

# Weight constants
_W_COST = 0.40
_W_QUALITY = 0.25
_W_TIME = 0.15
_W_COGNITIVE = 0.10
_W_DELEGATION = 0.10

# Normalisation bases
_COST_BASE = 10_000.0       # ₹10k savings = score 1.0 on cost axis
_TIME_BASE = 4.0            # 4 hours saved = score 1.0 on time axis
_QUALITY_PENALTY = 3.0      # quality_delta=-0.3 → score -0.9 on quality axis


class OptimizationScoringEngine:
    """Score a list of OptimizationOpportunities and return an evaluation."""

    def score(
        self,
        opportunities: list[OptimizationOpportunity],
    ) -> OptimizationEvaluation:
        if not opportunities:
            return OptimizationEvaluation(
                total_savings=0.0,
                execution_impact="No optimizations identified.",
                governance_risk="none",
                confidence_score=0.0,
                net_value_score=0.0,
            )

        total_savings = 0.0
        total_time_delta = 0.0
        total_quality_delta = 0.0
        cognitive_bonus = 0.0
        delegation_bonus = 0.0
        has_approval_risk = False
        confidence_sum = 0.0

        for opp in opportunities:
            w = opp.confidence_score
            delta = opp.estimated_cost_delta or 0.0
            total_savings -= delta * w        # savings = negative delta
            total_time_delta += (opp.estimated_time_delta or 0.0) * w
            total_quality_delta += (opp.estimated_quality_delta or 0.0) * w
            if opp.governance_impact == "requires_approval":
                has_approval_risk = True
            if opp.optimization_type == "cognitive":
                cognitive_bonus += 0.05 * w
            if opp.optimization_type == "delegation":
                delegation_bonus += 0.05 * w
            confidence_sum += w

        avg_confidence = confidence_sum / len(opportunities)

        # Normalised sub-scores
        cost_score = min(total_savings / _COST_BASE, 1.0)
        time_score = min(-total_time_delta / _TIME_BASE, 1.0)   # negative = faster = good
        quality_score = max(total_quality_delta * _QUALITY_PENALTY, -1.0)

        net = (
            _W_COST * cost_score
            + _W_QUALITY * quality_score
            + _W_TIME * time_score
            + _W_COGNITIVE * cognitive_bonus
            + _W_DELEGATION * delegation_bonus
        )
        net = max(-1.0, min(1.0, net))

        # Governance risk tier
        if has_approval_risk:
            gov_risk = "medium"
        elif any(o.optimization_type == "governance" for o in opportunities):
            gov_risk = "low"
        else:
            gov_risk = "none"

        # Execution impact narrative
        time_abs = abs(total_time_delta)
        if total_time_delta < -0.5:
            time_label = f"~{time_abs:.1f} hr faster"
        elif total_time_delta > 0.5:
            time_label = f"~{time_abs:.1f} hr commute added"
        else:
            time_label = "negligible time impact"

        if total_quality_delta < -0.15:
            quality_label = " · slight quality reduction"
        elif total_quality_delta > 0.1:
            quality_label = " · quality improves"
        else:
            quality_label = ""

        execution_impact = f"{time_label}{quality_label}"

        return OptimizationEvaluation(
            total_savings=total_savings,
            execution_impact=execution_impact,
            governance_risk=gov_risk,  # type: ignore[arg-type]
            confidence_score=avg_confidence,
            net_value_score=round(net, 3),
        )

    def rank(
        self,
        opportunities: list[OptimizationOpportunity],
    ) -> list[OptimizationOpportunity]:
        """Return opportunities ordered by individual net value (best first)."""
        def _opp_score(o: OptimizationOpportunity) -> float:
            cost_s = min(-(o.estimated_cost_delta or 0) / _COST_BASE, 1.0)
            time_s = min(-(o.estimated_time_delta or 0) / _TIME_BASE, 1.0)
            qual_s = max((o.estimated_quality_delta or 0) * _QUALITY_PENALTY, -1.0)
            return (cost_s * 0.5 + time_s * 0.3 + qual_s * 0.2) * o.confidence_score

        return sorted(opportunities, key=_opp_score, reverse=True)
