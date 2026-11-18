"""Versioned, fail-closed evaluation inputs. No credentials or provider imports."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Literal
from pydantic import Field, model_validator
from praxis.schemas import Dataset, Model

ROOT = Path(__file__).resolve().parents[3]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DatasetLabel(Model):
    path: str
    sha256: str
    reference_date: str
    metrics: dict[str, Any]
    mandatory: dict[str, list[str]]


class Change(Model):
    path: list[str | int] = Field(min_length=1)
    value: Any = None
    delete: bool = False


class Case(Model):
    id: str
    dataset: str
    question: str
    tags: list[str]
    scope: Literal['workflow', 'tool'] = 'workflow'
    template: str | None = None
    changes: list[Change] = Field(default_factory=list)
    record_changes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    calls: list[dict[str, Any]] = Field(default_factory=list)
    failure: Literal['timeout', 'rate_limit', 'cooldown', 'tool_failure',
        'malformed_tool', 'chief_timeout', 'interrupted'] | None = None
    expected_status: Literal['accepted', 'rejected', 'failed']
    expected_error: str | None = None
    expected_detections: list[str] = Field(default_factory=list)
    required_sources: dict[str, list[str]] = Field(default_factory=dict)
    allowed_sources: dict[str, list[str]] = Field(default_factory=dict)
    required_findings: list[str] = Field(default_factory=list)
    forbidden_priorities: list[str] = Field(default_factory=list)
    priority_count: int | None = None
    text_checks: list[dict[str, Any]] = Field(default_factory=list)
    forbidden_text: list[str] = Field(default_factory=list)
    expected_tool_result: dict[str, Any] | None = None
    live_eligible: bool = False


class Suite(Model):
    schema_version: Literal[1]
    version: str
    provenance: str
    datasets: dict[str, DatasetLabel]
    templates: dict[str, dict[str, Any]]
    cases: list[Case] = Field(min_length=1)
    thresholds: dict[str, float]

    @model_validator(mode='after')
    def coherent(self):
        ids = [c.id for c in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate case IDs')
        for case in self.cases:
            if case.dataset not in self.datasets:
                raise ValueError('Unknown dataset label')
            if case.template and case.template not in self.templates:
                raise ValueError('Unknown candidate template')
        return self


def load_suite(path: str | Path) -> Suite:
    suite = Suite.model_validate_json(Path(path).read_text(encoding='utf-8'))
    for label in suite.datasets.values():
        source = ROOT / label.path
        if digest(source) != label.sha256:
            raise ValueError('Dataset fingerprint mismatch: version and review labels before running')
        data = Dataset.model_validate_json(source.read_text(encoding='utf-8'))
        if str(data.reference_date) != label.reference_date:
            raise ValueError('Dataset reference date mismatch')
    return suite


def case_data(suite: Suite, case: Case) -> Dataset:
    raw = json.loads((ROOT / suite.datasets[case.dataset].path).read_text(encoding='utf-8'))
    for record_id, updates in case.record_changes.items():
        row = next((r for r in raw['records'] if r['record_id'] == record_id), None)
        if row is None:
            raise ValueError('Unknown record mutation')
        row.update(updates)
    return Dataset.model_validate(raw)


def candidate(suite: Suite, case: Case) -> dict:
    raw = deepcopy(suite.templates.get(case.template, {}))
    for change in case.changes:
        node = raw
        for key in change.path[:-1]:
            node = node[key]
        if change.delete:
            del node[change.path[-1]]
        else:
            node[change.path[-1]] = deepcopy(change.value)
    return raw
