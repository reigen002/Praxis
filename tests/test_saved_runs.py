"""Offline persistence tests; the fixture is a mocked run, not a live evaluation."""
import json
from uuid import uuid4

import pytest

from praxis.data import load_dataset
from praxis.decisions import RulesProvider
from praxis.schemas import Analysis, Event, RunResult
from praxis.tools import BusinessTools
from test_decisions_validation import example_briefing


def result_fixture():
    business = BusinessTools(load_dataset())
    business.actor = 'Business Operations Analyst'
    business.get_business_updates()
    result = RunResult(run_id=str(uuid4()), question='Prepare my briefing',
        briefing=example_briefing(), analysis=Analysis(findings=[dict(record_id='INC-001',
            source_ids=['INC-001', 'CON-001'], observation='Renewal requires attention.')]),
        metrics=business.calculate_business_metrics(),
        decisions=[RulesProvider(business).evaluate(r) for r in business.dataset.records],
        events=[*business.events, Event(actor='Business Operations Analyst', kind='task', detail='Validated'),
            Event(actor='Chief of Staff', kind='task', detail='Validated')],
        model='mocked-test-model', elapsed_seconds=12)
    return business.dataset, result


def test_saved_run_survives_reload_with_original_provenance(tmp_path):
    from praxis.services.saved_runs import save_run, load_runs
    dataset, result = result_fixture()
    save_run(dataset, result, tmp_path)
    saved, warnings = load_runs(dataset, tmp_path)
    assert not warnings and len(saved) == 1
    assert saved[0].result == result
    assert saved[0].result.events == result.events
    assert saved[0].saved_at.tzinfo is not None
    # Save a newer genuine execution for this same question, rather than growing duplicates.
    result.run_id = str(uuid4())
    save_run(dataset, result, tmp_path)
    assert len(load_runs(dataset, tmp_path)[0]) == 1


def test_changed_evidence_or_reference_date_hides_saved_run(tmp_path):
    from datetime import timedelta
    from praxis.services.saved_runs import save_run, load_runs
    dataset, result = result_fixture()
    save_run(dataset, result, tmp_path)
    changed = dataset.model_copy(deep=True)
    changed.records[0].description += ' New evidence.'
    assert load_runs(changed, tmp_path)[0] == []
    changed = dataset.model_copy(deep=True)
    changed.reference_date += timedelta(days=1)
    assert load_runs(changed, tmp_path)[0] == []


@pytest.mark.parametrize('mutation', ['sources', 'metrics', 'agents', 'retrieval'])
def test_unverified_run_is_not_saved(tmp_path, mutation):
    from praxis.services.saved_runs import save_run
    dataset, result = result_fixture()
    if mutation == 'sources':
        result.briefing.priorities[0].source_ids.append('FAKE-001')
    elif mutation == 'metrics':
        result.metrics.open_issues += 1
    elif mutation == 'agents':
        result.events = [e for e in result.events if e.actor != 'Chief of Staff']
    else:
        result.events = [e for e in result.events if e.kind != 'tool']
    with pytest.raises(ValueError):
        save_run(dataset, result, tmp_path)
    assert not list(tmp_path.glob('*.json'))


def test_corrupted_saved_result_is_withheld_without_breaking_others(tmp_path):
    from praxis.services.saved_runs import save_run, load_runs
    dataset, result = result_fixture()
    save_run(dataset, result, tmp_path)
    path = next(tmp_path.glob('*.json'))
    payload = json.loads(path.read_text())
    payload['result']['metrics']['open_issues'] = 999
    path.write_text(json.dumps(payload))
    saved, warnings = load_runs(dataset, tmp_path)
    assert saved == [] and warnings


def test_saved_runs_api_never_starts_agents(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import praxis.api as api
    from praxis.services.saved_runs import save_run
    dataset, result = result_fixture()
    save_run(dataset, result, tmp_path)
    monkeypatch.setattr(api, 'SAVED_RUNS', tmp_path)
    monkeypatch.setattr(api, 'run_briefing', lambda *a, **k: pytest.fail('Opening a saved run must not call a provider'))
    response = TestClient(api.app).get('/api/saved-runs?dataset=original')
    assert response.status_code == 200
    assert response.json()['runs'][0]['result']['run_id'] == result.run_id
    assert TestClient(api.app).get('/api/saved-runs?dataset=../../.env').status_code == 404


def test_read_only_jev_endpoint_cannot_spend_on_a_cache_miss(monkeypatch):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    import praxis.api as api
    monkeypatch.setattr(api, 'get_provider', lambda *args: SimpleNamespace(
        get_cached=lambda record: None,
        evaluate=lambda record: pytest.fail('Read-only saved decision endpoint cannot evaluate')))
    response = TestClient(api.app).get('/api/decisions/cached?dataset=demo&record_id=INC-001')
    assert response.status_code == 404
    assert 'No matching saved JEV decision' in response.json()['detail']


def test_save_failure_keeps_accepted_live_result_available(monkeypatch):
    import praxis.api as api
    from praxis.config import Settings
    dataset, result = result_fixture()
    monkeypatch.setattr(api, '_jobs', {'test': {'status': 'queued'}})
    monkeypatch.setattr(api, 'run_briefing', lambda *args: result)
    def fail(*args):
        raise OSError('PRIVATE path')
    monkeypatch.setattr(api, 'save_run', fail)
    api.perform_run('test', api.RunRequest(question='Brief me'), dataset, Settings('groq', 'test', 'private'))
    assert api._jobs['test']['status'] == 'completed'
    assert api._jobs['test']['result']['run_id'] == result.run_id
    assert 'Export it' in api._jobs['test']['save_warning']
    assert 'PRIVATE' not in api._jobs['test']['save_warning']
