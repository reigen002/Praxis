from decimal import Decimal
from fastapi.testclient import TestClient
from praxis.api import app


def test_overview_is_real_data_and_never_exposes_keys():
    client = TestClient(app)
    response = client.get('/api/overview?dataset=original')
    assert response.status_code == 200
    body = response.json()
    assert len(body['records']) == 28
    assert Decimal(body['metrics']['exposure_by_currency']['USD']) == Decimal('84000')
    assert body['policy']['escalations'][0]['record_id'] == 'INC-001'
    assert 'api_key' not in body['readiness']['llm']
    assert 'api_key' not in body['readiness']['jev']


def test_unknown_dataset_and_record_are_rejected():
    client = TestClient(app)
    assert client.get('/api/overview?dataset=../../.env').status_code == 404
    assert client.get('/api/records/NOPE?dataset=original').status_code == 404


def test_run_rejects_empty_question_before_model_call():
    client = TestClient(app)
    assert client.post('/api/runs', json={'question': ' ', 'dataset': 'original'}).status_code == 422


def test_record_evidence_includes_related_contract():
    response = TestClient(app).get('/api/records/INC-001?dataset=original')
    assert response.status_code == 200
    assert 'CON-001' in response.json()['source_ids']


def test_jev_safe_error_preserves_do_not_retry_warning(monkeypatch):
    from praxis.decisions.jev import JevError
    class Unavailable:
        def get_cached(self, record):
            raise JevError('JEV answered but its cache could not be saved. Do not retry a paid decision.', code='cache_write_error')
    monkeypatch.setattr('praxis.api.get_provider', lambda *args: Unavailable())
    response = TestClient(app).post('/api/decisions/evaluate', json={'dataset': 'original', 'record_id': 'INC-001'})
    assert response.status_code == 502
    assert 'Do not retry' in response.json()['detail']


def test_job_runs_in_background_and_second_submission_is_blocked(monkeypatch):
    import praxis.api as api
    from types import SimpleNamespace
    from praxis.config import Settings
    queued = []
    class Executor:
        def submit(self, *args):
            queued.append(args)
    monkeypatch.setattr(api, '_jobs', {})
    monkeypatch.setattr(api, '_executor', Executor())
    monkeypatch.setattr(api, 'settings', lambda: Settings('groq', 'test', 'private-test-key'))
    monkeypatch.setattr(api, 'save_run', lambda *args: None)
    monkeypatch.setattr(api, 'run_briefing', lambda *args: SimpleNamespace(model_dump=lambda **kwargs: {'run_id': 'validated-test-result'}))
    client = TestClient(app)
    started = client.post('/api/runs', json={'question': 'Priorities?', 'dataset': 'demo'})
    assert started.status_code == 202 and started.json()['status'] == 'queued'
    assert client.post('/api/runs', json={'question': 'Another run?'}).status_code == 409
    callback, *args = queued[0]
    callback(*args)
    finished = client.get('/api/runs/' + started.json()['id']).json()
    assert finished['status'] == 'completed'
    assert finished['result']['run_id'] == 'validated-test-result'
    assert finished['finished_at']
    assert 'private-test-key' not in str(finished)


def test_failed_job_exposes_safe_error_and_real_recorded_events(monkeypatch):
    import praxis.api as api
    from praxis.schemas import Event
    from praxis.services.briefing import BriefingFailed
    from praxis.config import Settings
    monkeypatch.setattr(api, '_jobs', {'test': {'status': 'queued'}})
    def fail(*args):
        raise BriefingFailed('Provider quota reached.', [Event(actor='Application', kind='error', detail='Rate limit')])
    monkeypatch.setattr(api, 'run_briefing', fail)
    api.perform_run('test', api.RunRequest(question='Test'), None, Settings('groq', 'test', 'private-test-key'))
    body = TestClient(app).get('/api/runs/test').json()
    assert body['status'] == 'failed' and body['error'] == 'Provider quota reached.'
    assert body['events'][0]['detail'] == 'Rate limit'


def test_cached_jev_result_does_not_make_an_evaluation_call(monkeypatch):
    import praxis.api as api
    from praxis.schemas import DecisionResult
    cached = DecisionResult(record_id='INC-001', classification='Engineering', urgency='Critical',
        urgency_score=2.81, provider='jev-ai.org', cache_hit=True, uncertainty='Mocked provider fixture only.')
    class Cached:
        def get_cached(self, record):
            return cached
        def evaluate(self, record):
            raise AssertionError('A saved result must never spend another call')
    monkeypatch.setattr(api, 'get_provider', lambda *args: Cached())
    response = TestClient(app).post('/api/decisions/evaluate', json={'dataset': 'demo', 'record_id': 'INC-001'})
    assert response.status_code == 200 and response.json()['cached'] is True
    assert response.json()['jev']['urgency_score'] == 2.81
