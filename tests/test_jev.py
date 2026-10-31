"""JEV wire contract and bounded failure behavior; no live provider calls."""
import json
import re
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest

from praxis.config import Settings
from praxis.data import load_dataset
from praxis.decisions import get_provider
from praxis.schemas import Analysis
from praxis.services.briefing import BriefingFailed, run_briefing
from praxis.tools import BusinessTools
from test_decisions_validation import example_briefing


def response_body():
    return {
        'id': 'dec_test123', 'model': 'jev-1.13',
        'model_version': 'jev-1.13-20260917', 'provider': 'jev-ai.org',
        'answers': {
            'team': {'type': 'choice', 'choice': 'Engineering', 'probabilities': {
                'Customer Success': 0.1, 'Sales': 0.02, 'Engineering': 0.8,
                'Finance': 0.01, 'Operations': 0.02, 'Human Review': 0.05}, 'confidence': 0.8},
            'urgency': {'type': 'score', 'score': 1.89,
                'legend': {'0': 'Routine', '1': 'Needs Attention', '2': 'Time Sensitive', '3': 'Critical'},
                'probabilities': {'0': 0, '1': 0.11, '2': 0.89, '3': 0}, 'confidence': 0.89},
            'renewal_risk': {'type': 'noul', 'noul': 0.87},
        },
        'usage': {'input_tokens': 503, 'output_tokens': 70, 'charged_tokens': 503,
            'charged_credits': 0, 'wallet': 'tokens'}, 'latency_ms': 1056,
    }


def make_provider(handler, *, delays=None):
    from praxis.decisions.jev import JevProvider
    tools = BusinessTools(load_dataset())
    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = JevProvider(tools, api_key='jev-test-key', client=client,
        sleep=(delays if delays is not None else []).append)
    return provider, tools, client


def test_jev_selection_uses_environment_key_without_calling_provider(monkeypatch):
    monkeypatch.setenv('JEV_API_KEY', 'jev-test-key')
    monkeypatch.setattr('praxis.decisions.load_dotenv', lambda: None, raising=False)
    provider = get_provider('jev', BusinessTools(load_dataset()))
    assert type(provider).__name__ == 'JevProvider'


def test_wire_contract_preserves_fractional_scores_evidence_and_metadata():
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=response_body(), headers={'X-Request-ID': 'dec_test123'})
    provider, tools, client = make_provider(respond)
    with client:
        result = provider.evaluate(tools.by_id['INC-001'])
    request = requests[0]
    body = json.loads(request.content)
    assert str(request.url) == 'https://jev-ai.org/api/v1/systemone/'
    assert request.headers['authorization'] == 'Bearer jev-test-key'
    assert re.fullmatch(r'[A-Za-z0-9._:-]{8,255}', request.headers['idempotency-key'])
    assert request.extensions['timeout']['read'] == 30
    assert request.extensions['timeout']['connect'] == 5
    assert body['model'] == 'jev-1.13'
    assert body['state']['reference_date'] == '2026-10-29'
    assert body['state']['record']['record_id'] == 'INC-001'
    assert {r['record_id'] for r in body['state']['related_records']} == {'CON-001', 'NOTE-001', 'NOTE-002'}
    contract = next(r for r in body['state']['related_records'] if r['record_id'] == 'CON-001')
    assert contract['contract_value'] == '48000.00'
    questions = body['questions']
    assert questions['team']['type'] == 'choice'
    assert set(questions['team']['criteria']) == {
        'Customer Success', 'Sales', 'Engineering', 'Finance', 'Operations', 'Human Review'}
    assert all(isinstance(v, str) for v in questions['team']['criteria'].values())
    assert questions['urgency']['type'] == 'score'
    assert questions['urgency']['criteria'] == ['Routine', 'Needs Attention', 'Time Sensitive', 'Critical']
    assert questions['renewal_risk']['type'] == 'noul'
    assert 'criteria' not in questions['renewal_risk']
    assert result.classification == 'Engineering'
    assert result.urgency_score == 1.89
    assert result.urgency == 'Time Sensitive'
    assert result.risk_probability == 0.87
    assert result.probabilities['Engineering'] == 0.8
    assert result.urgency_probabilities == {'0': 0, '1': 0.11, '2': 0.89, '3': 0}
    assert result.team_confidence == 0.8
    assert result.urgency_confidence == 0.89
    assert result.model == 'jev-1.13'
    assert result.model_version == 'jev-1.13-20260917'
    assert result.provider == 'jev-ai.org'
    assert result.request_id == 'dec_test123'
    assert result.usage == response_body()['usage']
    assert result.latency_ms == 1056
    assert result.uncertainty and not result.fallback


def test_urgency_label_uses_winning_tier_without_rounding_expected_score():
    body = response_body()
    body['answers']['urgency'].update(score=1.4, confidence=0.4,
        probabilities={'0': 0.4, '1': 0.1, '2': 0.2, '3': 0.3})
    provider, tools, client = make_provider(lambda _: httpx.Response(200, json=body))
    with client:
        result = provider.evaluate(tools.by_id['INC-001'])
    assert result.urgency == 'Routine'
    assert result.urgency_score == 1.4
    # Raw JEV signals remain independent; mandatory policy is enforced downstream.
    assert tools.get_policy_escalations().escalations[0].record_id == 'INC-001'


@pytest.mark.parametrize('path,value', [
    (('team', 'choice'), 'Unknown Team'),
    (('team', 'choice'), 'Sales'),
    (('team', 'probabilities', 'Engineering'), 1.8),
    (('team', 'probabilities', 'Sales'), -0.1),
    (('team', 'probabilities', 'Sales'), '0.02'),
    (('team', 'confidence'), float('nan')),
    (('urgency', 'score'), 2),  # Must equal the distribution's expected position.
    (('urgency', 'score'), 3.1),
    (('urgency', 'probabilities', '2'), 0.6),
    (('urgency', 'probabilities', '2'), float('inf')),
    (('urgency', 'legend', '2'), 'Critical'),
    (('renewal_risk', 'noul'), 1.01),
    (('renewal_risk', 'noul'), True),
])
def test_invalid_answers_fail_without_fallback(path, value):
    from praxis.decisions.jev import JevError
    body = response_body()
    target = body['answers']
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    # content= permits deliberately invalid NaN/Infinity JSON numeric tokens.
    provider, tools, client = make_provider(lambda _: httpx.Response(200,
        content=json.dumps(body), headers={'X-Request-ID': 'dec_bad123'}))
    with client, pytest.raises(JevError, match='invalid response') as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert error.value.request_id == 'dec_bad123'
    assert error.value.code == 'invalid_response'


@pytest.mark.parametrize('status,code', [
    (429, 'rate_limit_exceeded'), (499, 'request_cancelled'),
    (502, 'upstream_unreachable'), (503, 'service_unavailable'), (504, 'upstream_timeout'),
])
def test_retryable_errors_recover_using_one_idempotency_key(status, code):
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(status, json={'error': {'code': code}}, headers={'Retry-After': '2'})
        return httpx.Response(200, json=response_body())
    provider, tools, client = make_provider(respond, delays=delays)
    with client:
        assert provider.evaluate(tools.by_id['INC-001']).request_id == 'dec_test123'
    assert len(attempts) == 2
    assert delays == [2]
    assert len({r.headers['idempotency-key'] for r in attempts}) == 1
    assert attempts[0].content == attempts[1].content


@pytest.mark.parametrize('retry_after,expected', [('3', 3), ('invalid', 0.5), ('-1', 0.5), ('nan', 0.5)])
def test_retry_delay_is_bounded_and_falls_back_to_exponential(retry_after, expected):
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        if len(attempts) < 2:
            return httpx.Response(503, json={'error': {'code': 'service_unavailable'}},
                headers={'Retry-After': retry_after})
        return httpx.Response(200, json=response_body())
    provider, tools, client = make_provider(respond, delays=delays)
    with client:
        provider.evaluate(tools.by_id['INC-001'])
    assert delays == [expected]


def test_long_retry_after_stops_without_retrying_before_the_provider_allows():
    from praxis.decisions.jev import JevError
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        return httpx.Response(429, json={'error': {'code': 'rate_limit_exceeded'}},
            headers={'Retry-After': '900'})
    provider, tools, client = make_provider(respond, delays=delays)
    with client, pytest.raises(JevError, match='Wait before retrying'):
        provider.evaluate(tools.by_id['INC-001'])
    assert len(attempts) == 1 and delays == []


@pytest.mark.parametrize('status,code', [(400, 'invalid_request_error'), (401, 'invalid_api_key'),
    (402, 'insufficient_quota'), (404, 'model_not_found'), (413, 'request_too_large'),
    (422, 'input_too_large'), (429, 'api_key_spend_limit_exceeded'), (429, 'unknown_code')])
def test_auth_quota_and_invalid_requests_are_not_retried_or_leaked(status, code):
    from praxis.decisions.jev import JevError
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        return httpx.Response(status, json={'error': {'code': code,
            'message': 'SECRET Bearer jev-test-key'}}, headers={'X-Request-ID': 'dec_error123'})
    provider, tools, client = make_provider(respond, delays=delays)
    with client, pytest.raises(JevError) as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert len(attempts) == 1 and not delays
    assert error.value.status_code == status
    assert error.value.request_id == 'dec_error123'
    assert 'SECRET' not in str(error.value) and 'jev-test-key' not in str(error.value)


def test_openrouter_key_is_rejected_before_any_jev_http_request():
    from praxis.decisions.jev import JevError, JevProvider
    tools = BusinessTools(load_dataset())
    def unexpected_request(request):
        pytest.fail('An OpenRouter credential must not be sent to the JEV host')
    with httpx.Client(transport=httpx.MockTransport(unexpected_request)) as client:
        provider = JevProvider(tools, api_key='sk-or-v1-test-only-not-a-real-key', client=client)
        with pytest.raises(JevError, match='OpenRouter') as error:
            provider.evaluate(tools.by_id['INC-001'])
    assert error.value.code == 'credential_provider_mismatch'
    assert 'sk-or-v1-test-only-not-a-real-key' not in str(error.value)


@pytest.mark.parametrize('reason,expected', [
    ('missing_bearer', 'Bearer'), ('empty_token', 'empty'),
    ('unknown_key', 'not recognized'), ('wrong_key_type', 'management key'),
    ('disabled', 'disabled'), ('revoked', 'revoked')])
def test_jev_auth_reason_is_safe_actionable_and_not_retried(reason, expected):
    from praxis.decisions.jev import JevError
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        return httpx.Response(401, json={'error': {'code': 'invalid_api_key',
            'reason': reason, 'message': 'SECRET jev-test-key'}})
    provider, tools, client = make_provider(respond, delays=delays)
    with client, pytest.raises(JevError) as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert error.value.reason == reason and expected in str(error.value)
    assert len(attempts) == 1 and not delays
    assert 'SECRET' not in str(error.value) and 'jev-test-key' not in str(error.value)


def test_unknown_auth_reason_is_not_reflected_into_errors():
    from praxis.decisions.jev import JevError
    provider, tools, client = make_provider(lambda _: httpx.Response(401,
        json={'error': {'code': 'invalid_api_key', 'reason': 'SECRET jev-test-key'}}))
    with client, pytest.raises(JevError) as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert error.value.reason is None
    assert 'SECRET' not in str(error.value) and 'jev-test-key' not in str(error.value)


def test_timeouts_stop_after_three_attempts_without_exposing_transport_details():
    from praxis.decisions.jev import JevError
    attempts, delays = [], []
    def respond(request):
        attempts.append(request)
        raise httpx.ReadTimeout('SECRET Bearer jev-test-key', request=request)
    provider, tools, client = make_provider(respond, delays=delays)
    with client, pytest.raises(JevError, match='timed out') as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert len(attempts) == 3 and delays == [0.5, 1]
    assert len({r.headers['idempotency-key'] for r in attempts}) == 1
    assert 'SECRET' not in str(error.value) and 'jev-test-key' not in str(error.value)


@pytest.mark.parametrize('status_url', ['https://jev-ai.org/api/v1/requests/dec_original/',
    'https://untrusted.example/collect', 'http://jev-ai.org/api/v1/requests/dec_original/'])
def test_conflict_is_explicit_and_does_not_replay_or_leak_credentials(status_url):
    from praxis.decisions.jev import JevError
    attempts = []
    def respond(request):
        attempts.append(request)
        if request.method == 'GET':
            assert str(request.url) == 'https://jev-ai.org/api/v1/requests/dec_original/'
            return httpx.Response(200, json={'id': 'dec_original', 'status': 'success', 'credits_used': 1})
        return httpx.Response(409, json={'error': {'code': 'request_already_completed',
            'request_id': 'dec_original', 'status_url': status_url}}, headers={'X-Request-ID': 'dec_retry'})
    provider, tools, client = make_provider(respond)
    with client, pytest.raises(JevError, match='dec_original') as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert error.value.request_id == 'dec_original'
    assert 'completed' in str(error.value) and 'Rules' in str(error.value)
    assert [r.method for r in attempts] == ['POST', 'GET']


def test_timeout_then_conflict_keeps_original_request_across_restart(tmp_path):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    requests = []
    cache = tmp_path / 'jev-decisions.json'
    def respond(request):
        requests.append(request)
        if len(requests) == 1:
            # A process crash must also leave the original idempotency key on disk.
            assert request.headers['idempotency-key'] in cache.read_text()
            raise httpx.ReadTimeout('PRIVATE', request=request)
        if request.method == 'POST':
            return httpx.Response(409, json={'error': {'code': 'request_already_completed',
                'request_id': 'dec_original', 'status_url': 'https://untrusted.example/'}})
        return httpx.Response(200, json={'id': 'dec_original', 'status': 'success', 'credits_used': 1})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache, sleep=lambda _: None)
        with pytest.raises(JevError, match='completed'):
            provider.evaluate(tools.by_id['INC-001'])
        restarted = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache)
        assert restarted.get_cached(tools.by_id['INC-001']) is None
        with pytest.raises(JevError, match='completed'):
            restarted.evaluate(tools.by_id['INC-001'])
    assert [r.method for r in requests] == ['POST', 'POST', 'GET', 'GET']
    assert len({r.headers['idempotency-key'] for r in requests if r.method == 'POST'}) == 1
    assert 'jev-test-key' not in cache.read_text() and 'PRIVATE' not in cache.read_text()


@pytest.mark.parametrize('kind', ['timeout', 'redirect', 'mismatch', 'invalid', 'untrusted_status'])
def test_conflict_status_failure_never_exposes_private_data_or_reposts(kind):
    from praxis.decisions.jev import JevError
    requests = []
    def respond(request):
        requests.append(request)
        if request.method == 'POST':
            return httpx.Response(409, json={'error': {'code': 'request_in_progress', 'request_id': 'dec_original'}})
        if kind == 'timeout':
            raise httpx.ReadTimeout('SECRET jev-test-key', request=request)
        if kind == 'redirect':
            return httpx.Response(302, headers={'Location': 'https://untrusted.example/'})
        if kind == 'invalid':
            return httpx.Response(200, text='SECRET jev-test-key')
        return httpx.Response(200, json={'id': 'dec_other' if kind == 'mismatch' else 'dec_original',
            'status': 'SECRET jev-test-key'})
    provider, tools, client = make_provider(respond)
    with client, pytest.raises(JevError, match='status could not be confirmed') as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert [r.method for r in requests] == ['POST', 'GET']
    assert 'SECRET' not in str(error.value) and 'jev-test-key' not in str(error.value)


def test_invalid_success_is_not_paid_for_again_after_restart(tmp_path):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    requests = []
    def respond(request):
        requests.append(request)
        if request.method == 'GET':
            return httpx.Response(200, json={'id': 'dec_bad', 'status': 'success'})
        return httpx.Response(200, json={'id': 'dec_bad', 'answers': 'invalid'})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        for _ in range(2):
            provider = JevProvider(tools, api_key='jev-test-key', client=client,
                cache_path=tmp_path / 'jev-decisions.json')
            with pytest.raises(JevError):
                provider.evaluate(tools.by_id['INC-001'])
    assert [r.method for r in requests] == ['POST', 'GET']


def test_unconfirmed_timeout_reuses_saved_key_after_restart(tmp_path):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    requests = []
    def respond(request):
        requests.append(request)
        raise httpx.ReadTimeout('PRIVATE', request=request)
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        for _ in range(2):
            provider = JevProvider(tools, api_key='jev-test-key', client=client,
                cache_path=tmp_path / 'jev-decisions.json', sleep=lambda _: None)
            with pytest.raises(JevError, match='timed out'):
                provider.evaluate(tools.by_id['INC-001'])
    assert len(requests) == 6
    assert len({r.headers['idempotency-key'] for r in requests}) == 1


def test_explicit_uncharged_auth_failure_allows_corrected_key_retry(tmp_path):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    requests = []
    cache = tmp_path / 'jev-decisions.json'
    def respond(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(401, json={'error': {'code': 'invalid_api_key'}})
        return httpx.Response(200, json=response_body())
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        wrong = JevProvider(tools, api_key='invalid-test-key', client=client, cache_path=cache)
        with pytest.raises(JevError):
            wrong.evaluate(tools.by_id['INC-001'])
        corrected = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache)
        assert corrected.evaluate(tools.by_id['INC-001']).provider == 'jev-ai.org'
    assert len(requests) == 2
    assert requests[0].headers['idempotency-key'] != requests[1].headers['idempotency-key']
    assert not json.loads(cache.read_text())['requests']


def test_request_journal_must_be_writable_before_spending(tmp_path, monkeypatch):
    from pathlib import Path
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    def fail_write(*args, **kwargs):
        raise PermissionError('PRIVATE')
    monkeypatch.setattr(Path, 'mkdir', fail_write)
    def never_call(request):
        pytest.fail('Do not spend if the original request cannot be tracked')
    with httpx.Client(transport=httpx.MockTransport(never_call)) as client:
        provider = JevProvider(tools, api_key='jev-test-key', client=client,
            cache_path=tmp_path / 'jev-decisions.json')
        with pytest.raises(JevError, match='tracking could not be saved'):
            provider.evaluate(tools.by_id['INC-001'])


@pytest.mark.parametrize('pending', [{'idempotency_key': 'bad'}, 'corrupt'])
def test_corrupt_request_journal_does_not_spend(tmp_path, pending):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    def never_call(request):
        pytest.fail('Invalid request tracking must fail closed')
    with httpx.Client(transport=httpx.MockTransport(never_call)) as client:
        cache = tmp_path / 'jev-decisions.json'
        provider = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache)
        fingerprint = provider._fingerprint(provider._body(tools.by_id['INC-001']))
        cache.write_text(json.dumps({'version': 1, 'decisions': {}, 'requests': {fingerprint: pending}}))
        with pytest.raises(JevError, match='saved JEV request is invalid'):
            provider.evaluate(tools.by_id['INC-001'])


@pytest.mark.parametrize('status,phrase', [('running', 'still processing'), ('failed', 'without a usable answer')])
def test_status_metadata_is_never_accepted_as_a_decision(status, phrase):
    from praxis.decisions.jev import JevError
    def respond(request):
        if request.method == 'POST':
            return httpx.Response(409, json={'error': {'code': 'request_in_progress', 'request_id': 'dec_original'}})
        return httpx.Response(200, json={'id': 'dec_original', 'status': status})
    provider, tools, client = make_provider(respond)
    with client, pytest.raises(JevError, match=phrase):
        provider.evaluate(tools.by_id['INC-001'])


def test_separate_evaluations_get_distinct_keys():
    keys = []
    def respond(request):
        keys.append(request.headers['idempotency-key'])
        return httpx.Response(200, json=response_body())
    provider, tools, client = make_provider(respond)
    with client:
        provider.evaluate(tools.by_id['INC-001'])
        provider.evaluate(tools.by_id['INC-001'])
    assert len(set(keys)) == 2


def test_operating_snapshot_preserves_record_money_and_missing_values():
    snapshot = BusinessTools(load_dataset()).get_operating_snapshot()
    updates = {r.record_id: r for r in snapshot.updates}
    assert updates['CON-001'].contract_value == Decimal('48000.00')
    assert updates['CON-001'].currency == 'USD'
    assert updates['CAN-002'].contract_value is None


def test_decision_failure_becomes_sanitized_briefing_failure_and_error_event(monkeypatch):
    def evaluate(record):
        raise RuntimeError('SECRET-auth-token provider response')
    monkeypatch.setattr('praxis.services.briefing.get_provider',
        lambda *args: SimpleNamespace(evaluate=evaluate))
    with pytest.raises(BriefingFailed) as error:
        run_briefing('Brief me', config=Settings('openai', 'test', 'test-key', decision_provider='jev'))
    assert 'SECRET' not in str(error.value)
    assert error.value.events[-1].kind == 'error'
    assert 'RuntimeError' in error.value.events[-1].detail
    assert 'SECRET' not in error.value.events[-1].detail


def test_successful_jev_run_logs_actual_provider_and_keeps_raw_signals(monkeypatch):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=response_body())
    provider, _, client = make_provider(respond)
    monkeypatch.setattr('praxis.services.briefing.get_provider', lambda *args: provider)
    def crew(business, config, decisions, question):
        business.actor = 'Business Operations Analyst'
        business.get_business_updates()
        analysis = Analysis(findings=[dict(record_id='INC-001', source_ids=['INC-001', 'CON-001'],
            observation='Integration remains unavailable.')])
        return SimpleNamespace(tasks=[SimpleNamespace(output=SimpleNamespace(pydantic=analysis))],
            kickoff=lambda: SimpleNamespace(pydantic=example_briefing()))
    monkeypatch.setattr('praxis.services.briefing.build_crew', crew)
    with client:
        result = run_briefing('Brief me', config=Settings('openai', 'test', 'test-key', decision_provider='jev'))
    assert result.decisions[0].urgency == 'Time Sensitive'
    assert result.briefing.priorities[0].urgency == 'Critical'
    assert len(calls) == 1
    assert {d.provider for d in result.decisions[1:]} == {'rules-v1'}
    decision_event = next(e for e in result.events if e.kind == 'decision')
    assert 'jev-ai.org' in decision_event.detail and 'jev-1.13-20260917' in decision_event.detail
    assert 'rules-v1' in decision_event.detail
    assert 'INC-001' in decision_event.detail


def test_saved_genuine_jev_result_is_reused_without_a_network_call(tmp_path):
    from praxis.decisions.jev import JevProvider
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=response_body())
    tools = BusinessTools(load_dataset())
    cache_path = tmp_path / 'jev-decisions.json'
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache_path)
        assert provider.get_cached(tools.by_id['INC-001']) is None
        first = provider.evaluate(tools.by_id['INC-001'])
        assert not first.cache_hit and first.evaluated_at is not None
        # A new provider instance simulates the next browser session or server restart.
        next_provider = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache_path)
        saved = next_provider.get_cached(tools.by_id['INC-001'])
        assert saved.cache_hit and saved.request_id == 'dec_test123'
        second = next_provider.evaluate(tools.by_id['INC-001'])
    assert len(requests) == 1
    assert second.cache_hit and second.evaluated_at == first.evaluated_at
    assert second.model_version == first.model_version
    assert second.probabilities == first.probabilities
    assert 'jev-test-key' not in cache_path.read_text(encoding='utf-8')


def test_cache_fingerprint_includes_related_evidence_and_reference_date(tmp_path):
    from datetime import date
    from praxis.decisions.jev import JevProvider
    tools = BusinessTools(load_dataset())
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=response_body())
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        provider = JevProvider(tools, api_key='jev-test-key', client=client,
            cache_path=tmp_path / 'jev-decisions.json')
        provider.evaluate(tools.by_id['INC-001'])
        tools.by_id['NOTE-001'].description = 'New conflicting evidence changed after the saved decision.'
        assert provider.get_cached(tools.by_id['INC-001']) is None
        provider.evaluate(tools.by_id['INC-001'])
        tools.dataset.reference_date = date(2026, 10, 30)
        assert provider.get_cached(tools.by_id['INC-001']) is None
    assert len(requests) == 2


def test_corrupt_cache_fails_explicitly_without_spending_again(tmp_path):
    from praxis.decisions.jev import JevProvider, JevError
    tools = BusinessTools(load_dataset())
    cache_path = tmp_path / 'jev-decisions.json'
    cache_path.write_text('{corrupt', encoding='utf-8')
    def never_call(request):
        pytest.fail('A corrupt cache must not silently cause another paid request')
    with httpx.Client(transport=httpx.MockTransport(never_call)) as client:
        provider = JevProvider(tools, api_key='jev-test-key', client=client, cache_path=cache_path)
        with pytest.raises(JevError, match='cache'):
            provider.evaluate(tools.by_id['INC-001'])


def test_configured_target_gets_the_only_jev_call(monkeypatch):
    targets = []
    provider, _, client = make_provider(lambda request: httpx.Response(200, json=response_body()))
    def evaluate(record):
        targets.append(record.record_id)
        return provider.evaluate(record)
    monkeypatch.setattr('praxis.services.briefing.get_provider',
        lambda *args: SimpleNamespace(evaluate=evaluate))
    # Stop after decisions: this isolates JEV budget selection from the generative provider.
    def finish(*args, **kwargs):
        raise RuntimeError('Stop before any generative model call')
    monkeypatch.setattr('praxis.services.briefing.build_crew', finish)
    with client, pytest.raises(BriefingFailed):
        run_briefing('Brief me', config=Settings('openai', 'test', 'test-key',
            decision_provider='jev', jev_record_id='FEAT-001'))
    assert targets == ['FEAT-001']


def test_unknown_target_fails_before_any_jev_call(monkeypatch):
    def never_evaluate(record):
        pytest.fail('Invalid target must not reach a paid provider')
    monkeypatch.setattr('praxis.services.briefing.get_provider',
        lambda *args: SimpleNamespace(evaluate=never_evaluate))
    with pytest.raises(BriefingFailed, match='does not exist') as error:
        run_briefing('Brief me', config=Settings('openai', 'test', 'test-key',
            decision_provider='jev', jev_record_id='FAKE-001'))
    assert error.value.events[-1].kind == 'error'


def test_retries_stop_after_three_retryable_http_failures():
    from praxis.decisions.jev import JevError
    requests, delays = [], []
    def respond(request):
        requests.append(request)
        return httpx.Response(503, json={'error': {'code': 'service_unavailable'}},
            headers={'X-Request-ID': 'dec_exhausted'})
    provider, tools, client = make_provider(respond, delays=delays)
    with client, pytest.raises(JevError) as error:
        provider.evaluate(tools.by_id['INC-001'])
    assert len(requests) == 3 and delays == [0.5, 1]
    assert error.value.request_id == 'dec_exhausted'


def test_redirect_cannot_forward_jev_authorization_to_another_origin():
    from praxis.decisions.jev import JevError
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(307, headers={'Location': 'https://untrusted.example/collect'})
    provider, tools, client = make_provider(respond)
    client.follow_redirects = True
    with client, pytest.raises(JevError):
        provider.evaluate(tools.by_id['INC-001'])
    assert len(requests) == 1
    assert requests[0].url.host == 'jev-ai.org'
