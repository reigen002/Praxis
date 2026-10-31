"""Bounded routing and urgency signals; no generative output or side effects."""
from typing import Protocol
from dotenv import load_dotenv
from praxis.schemas import DecisionResult, Record
from praxis.tools import BusinessTools

LEVELS = ['Routine', 'Needs Attention', 'Time Sensitive', 'Critical']
ROUTING = {'support': 'Engineering', 'contract': 'Customer Success', 'sales': 'Sales',
    'feature': 'Engineering', 'product': 'Engineering', 'cancellation': 'Customer Success',
    'operations': 'Operations', 'finance': 'Finance', 'routine': 'Operations', 'note': 'Human Review'}


class DecisionProvider(Protocol):
    def evaluate(self, record: Record) -> DecisionResult: ...


class RulesProvider:
    def __init__(self, tools: BusinessTools):
        self.reference_date = tools.dataset.reference_date
        self.mandatory = {e.record_id for e in tools.get_policy_escalations().escalations}

    def evaluate(self, record: Record) -> DecisionResult:
        score = 0
        if record.active:
            if record.category not in ('routine', 'note', 'feature'):
                score = 1
            if record.deadline and (record.deadline - self.reference_date).days <= 3:
                score = 2
            if record.record_id in self.mandatory:
                score = 3
        return DecisionResult(record_id=record.record_id, classification=ROUTING[record.category],
            urgency=LEVELS[score], urgency_score=score, provider='rules-v1',
            uncertainty='Deterministic heuristic; no calibrated confidence or probability. Missing or conflicting evidence requires human review.')


def get_provider(name: str, tools: BusinessTools) -> DecisionProvider:
    if name == 'rules':
        return RulesProvider(tools)
    if name == 'jev':
        from praxis.decisions.jev import JevProvider
        load_dotenv()
        return JevProvider(tools, cache_path='artifacts/jev-decisions.json')
    raise ValueError('Unsupported decision provider')
