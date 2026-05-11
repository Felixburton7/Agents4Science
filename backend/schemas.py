from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ParsedHypothesis(BaseModel):
    claim: str
    mechanism: str
    context: str
    population: str
    method: str


class Paper(BaseModel):
    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    abstract: str = ""
    url: str = ""
    citation_count: int = 0
    relevance_score: float = 0.0
    cluster: str = "unclustered"


class Conflict(BaseModel):
    paper_id: str
    title: str
    disagreement_dimension: str
    explanation: str
    severity: float = Field(ge=0.0, le=1.0)


class OverlapReport(BaseModel):
    crowding_score: int = Field(ge=0, le=100)
    overlapping_papers: List[str] = Field(default_factory=list)
    whitespace_summary: str
    risk_notes: List[str] = Field(default_factory=list)


class ResearchGroup(BaseModel):
    group_id: str
    name: str
    institution: str
    principal_investigators: List[str] = Field(default_factory=list)
    recent_paper_ids: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    grounding_evidence: str


class EmulatorOutput(BaseModel):
    group_id: str
    group_name: str
    interest_score: int = Field(ge=0, le=100)
    engagement_type: str
    proposed_direction: str
    method_they_use: str
    time_to_publish_months: int = Field(ge=0)
    competitive_risk: int = Field(ge=0, le=100)
    grounding_paper_ids: List[str] = Field(default_factory=list)


class Scenario(BaseModel):
    scenario_id: str
    name: str
    probability: float = Field(ge=0.0, le=1.0)
    description: str
    leading_groups: List[str] = Field(default_factory=list)
    implications: List[str] = Field(default_factory=list)


class ImpactDimension(BaseModel):
    score: int = Field(ge=0, le=100)
    confidence_low: int = Field(ge=0, le=100)
    confidence_high: int = Field(ge=0, le=100)
    rationale: str


class ImpactForecast(BaseModel):
    volume: ImpactDimension
    velocity: ImpactDimension
    reach: ImpactDimension
    depth: ImpactDimension
    disruption: ImpactDimension
    translation: ImpactDimension
    overall_summary: str


class MetricScore(BaseModel):
    metric_name: str
    score: int = Field(ge=0, le=100)
    confidence_low: int = Field(ge=0, le=100)
    confidence_high: int = Field(ge=0, le=100)
    rationale: str
    evidence: List[str] = Field(default_factory=list)
    weakness: str = ""


class Scorecard(BaseModel):
    composite_score: int = Field(ge=0, le=100)
    verdict: str
    metric_scores: List[MetricScore] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    evidence_summary: str


class Variant(BaseModel):
    variant_id: str
    hypothesis_text: str
    operator: str
    rationale: str
    impact_scores: Dict[str, int] = Field(default_factory=dict)
    composite_score: int = Field(default=0, ge=0, le=100)
    scorecard: Optional[Scorecard] = None
    rank: Optional[int] = None
    is_pareto_selected: bool = False
    dominance_explanation: str = ""


class GroundednessCheck(BaseModel):
    group_id: str
    group_name: str
    is_grounded: bool
    flagged_inconsistencies: List[str] = Field(default_factory=list)
    evidence: str


class StrategyMemo(BaseModel):
    recommendation: str
    executive_summary: str
    key_findings: List[str] = Field(default_factory=list)
    selected_variants: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        sections = [
            "# Strategy Memo",
            f"## Recommendation\n{self.recommendation}",
            f"## Executive Summary\n{self.executive_summary}",
            _bullets("Key Findings", self.key_findings),
            _bullets("Selected Variants", self.selected_variants),
            _bullets("Risks", self.risks),
            _bullets("Next Steps", self.next_steps),
        ]
        return "\n\n".join(section for section in sections if section)


def _bullets(title: str, values: List[str]) -> str:
    if not values:
        return ""
    body = "\n".join(f"- {value}" for value in values)
    return f"## {title}\n{body}"
