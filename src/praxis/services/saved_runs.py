"""Persist accepted executions for honest, repeatable local review. No provider calls."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Literal

from pydantic import AwareDatetime
from praxis.schemas import Dataset, Model, RunResult
from praxis.tools import BusinessTools
from praxis.validation import validate_analysis, validate_briefing


class SavedRun(Model):
    schema_version: Literal[1] = 1
    dataset_fingerprint: str
    saved_at: AwareDatetime
    result: RunResult


def fingerprint(dataset: Dataset) -> str:
    return hashlib.sha256(json.dumps(dataset.model_dump(mode='json'),
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_saved_result(dataset: Dataset, result: RunResult):
    business = BusinessTools(dataset)
    if business.calculate_business_metrics() != result.metrics:
        raise ValueError('Saved metrics do not match the dataset')
    business.events = list(result.events)
    tasks = {e.actor for e in result.events if e.kind == 'task'}
    if not {'Business Operations Analyst', 'Chief of Staff'} <= tasks:
        raise ValueError('Both completed agent tasks must be recorded')
    if any(set(e.source_ids) - business.by_id.keys() for e in result.events):
        raise ValueError('Execution event references unknown records')
    if {d.record_id for d in result.decisions} != business.by_id.keys():
        raise ValueError('Decision records do not match the dataset')
    validate_analysis(result.analysis, business)
    validate_briefing(result.briefing, business, result.analysis)


def save_run(dataset: Dataset, result: RunResult, directory: Path) -> SavedRun:
    validate_saved_result(dataset, result)
    saved = SavedRun(dataset_fingerprint=fingerprint(dataset),
        saved_at=datetime.now(timezone.utc), result=result)
    # Keep the latest accepted execution per question/provider/evidence combination.
    identity = saved.dataset_fingerprint + result.question.strip() + result.model + ','.join(
        sorted({d.provider for d in result.decisions}))
    filename = hashlib.sha256(identity.encode()).hexdigest() + '.json'
    directory.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=directory,
                prefix='saved-run-', suffix='.tmp', delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(saved.model_dump_json(indent=2))
        os.replace(temporary_path, directory / filename)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return saved


def load_runs(dataset: Dataset, directory: Path) -> tuple[list[SavedRun], list[str]]:
    saved, warnings = [], []
    current = fingerprint(dataset)
    for path in directory.glob('*.json'):
        try:
            item = SavedRun.model_validate_json(path.read_text(encoding='utf-8'))
            if item.dataset_fingerprint != current:
                continue
            validate_saved_result(dataset, item.result)
            saved.append(item)
        except (OSError, ValueError, TypeError):
            warnings.append('A saved briefing could not be verified and was withheld.')
    return sorted(saved, key=lambda item: item.saved_at, reverse=True), warnings
