"""Strict contracts shared by tools, agents, and presentation."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Category = Literal['support', 'contract', 'sales', 'feature', 'product', 'cancellation', 'operations', 'finance', 'routine', 'note']
Team = Literal['Customer Success', 'Sales', 'Engineering', 'Finance', 'Operations', 'Human Review']
Urgency = Literal['Routine', 'Needs Attention', 'Time Sensitive', 'Critical']


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Record(Model):
    record_id: str = Field(pattern=r'^[A-Z]+-\d{3}$')
    source: str
    category: Category
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    customer_or_team: str
    created_at: date
    deadline: date | None = None
    status: Literal['open', 'blocked', 'completed', 'cancelled'] = 'open'
    owner: Team | None = None
    contract_value: Decimal | None = Field(default=None, ge=0, decimal_places=2, allow_inf_nan=False)
    currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')
    contract_id: str | None = None
    severity: Literal['normal', 'high', 'critical'] = 'normal'
    related_record_ids: list[str] = Field(default_factory=list)

    @field_validator('currency', mode='before')
    @classmethod
    def normalize_currency(cls, value):
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode='after')
    def financial_integrity(self):
        if self.contract_value is not None and not self.currency:
            raise ValueError('Financial value requires currency')
        if self.category == 'contract' and not self.contract_id:
            raise ValueError('Contract record requires contract_id')
        return self

    @property
    def active(self):
        return self.status in ('open', 'blocked')


class Dataset(Model):
    label: Literal['SYNTHETIC DEMONSTRATION DATA']
    reference_date: date
    records: list[Record] = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def check_records(self):
        ids = [r.record_id for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate record IDs')
        contracts = set()
        for row in self.records:
            if row.created_at > self.reference_date:
                raise ValueError('Record created after reference date')
            if set(row.related_record_ids) - set(ids):
                raise ValueError('Unknown related record ID')
            if row.category == 'contract':
                if row.contract_id in contracts:
                    raise ValueError('Duplicate authoritative contract record')
                contracts.add(row.contract_id)
        return self


class RecordResult(Model):
    records: list[Record]
    source_ids: list[str]


class Metrics(Model):
    reference_date: date
    exposure_by_currency: dict[str, Decimal]
    pipeline_by_currency: dict[str, Decimal]
    open_issues: int
    overdue_tasks: int
    customer_escalations: int
    opportunities_awaiting_action: int
    missing_financial_ids: list[str]
    source_ids: list[str]
    cohorts: dict[str, list[str]]
    definitions: dict[str, str]


class DeadlineRisk(Model):
    record_id: str
    deadline: date
    days_remaining: int
    overdue: bool


class DeadlineResult(Model):
    reference_date: date
    window_days: int
    risks: list[DeadlineRisk]
    source_ids: list[str]


class Escalation(Model):
    record_id: str
    rule: str
    reason: str
    source_ids: list[str]


class EscalationResult(Model):
    escalations: list[Escalation]
    source_ids: list[str]


class UpdateSummary(Model):
    record_id: str
    category: Category
    title: str
    description: str
    status: str
    deadline: date | None = None
    severity: str
    related_record_ids: list[str]
    contract_value: Decimal | None = Field(default=None, ge=0, decimal_places=2, allow_inf_nan=False)
    currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')


class SnapshotMetrics(Model):
    exposure_by_currency: dict[str, Decimal]
    pipeline_by_currency: dict[str, Decimal]
    open_issues: int
    overdue_tasks: int
    customer_escalations: int
    opportunities_awaiting_action: int
    missing_financial_ids: list[str]
    source_ids: list[str]


class OperatingSnapshot(Model):
    reference_date: date
    updates: list[UpdateSummary]
    metrics: SnapshotMetrics
    deadlines: DeadlineResult
    policy: EscalationResult
    source_ids: list[str]


class Event(Model):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    kind: Literal['tool', 'task', 'decision', 'validation', 'error']
    tool: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    detail: str


class DecisionResult(Model):
    record_id: str
    classification: Team
    urgency: Urgency
    urgency_score: float = Field(ge=0, le=3)
    provider: str
    probabilities: dict[str, float] | None = None
    risk_probability: float | None = Field(default=None, ge=0, le=1)
    uncertainty: str
    error: str | None = None
    fallback: bool = False
    model: str | None = None
    model_version: str | None = None
    request_id: str | None = None
    team_confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    urgency_confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    urgency_probabilities: dict[str, float] | None = None
    usage: dict[str, int | float | str] | None = None
    latency_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    cache_hit: bool = False
    evaluated_at: datetime | None = None


class Finding(Model):
    record_id: str
    source_ids: list[str] = Field(min_length=1)
    observation: str
    assumptions: list[str] = Field(default_factory=list)


class Analysis(Model):
    findings: list[Finding] = Field(min_length=1, max_length=12)
    limitations: list[str] = Field(default_factory=list)


class Priority(Model):
    rank: int = Field(ge=1, le=10)
    record_id: str
    title: str
    category: Category
    urgency: Urgency
    business_impact: str
    recommended_action: str
    suggested_owner: Team
    source_ids: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class FollowUp(Model):
    record_id: str
    recipient_team: Team
    draft: str
    source_ids: list[str] = Field(min_length=1)
    approval_required: Literal[True] = True


class Briefing(Model):
    executive_summary: str = Field(min_length=1, max_length=1800)
    priorities: list[Priority] = Field(min_length=1, max_length=10)
    follow_ups: list[FollowUp] = Field(default_factory=list, max_length=5)
    data_limitations: list[str] = Field(default_factory=list)


class RunResult(Model):
    run_id: str
    question: str
    briefing: Briefing
    analysis: Analysis
    metrics: Metrics
    decisions: list[DecisionResult]
    events: list[Event]
    model: str
    mode: Literal['live'] = 'live'
    elapsed_seconds: float
