"""Mocked HTTP checks of real CrewAI/OpenAI SDK routing; no live Groq claims."""
import json
import httpx
import pytest
from openai import OpenAI
from praxis.agents import build_crew
from praxis.config import Settings
from praxis.data import load_dataset
from praxis.tools import BusinessTools
from praxis.schemas import Briefing
from test_decisions_validation import example_briefing


def groq_crew():
    return build_crew(BusinessTools(load_dataset()), Settings('groq',
        'openai/gpt-oss-120b', 'groq-test-only', 'https://api.groq.com/openai/v1'), [], 'Brief me')


def test_groq_wire_request_and_structured_response():
    captured = []
    def respond(request):
        captured.append((request, json.loads(request.content)))
        return httpx.Response(200, json=dict(id='mock-groq-completion', object='chat.completion',
            created=0, model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason='stop',
            message=dict(role='assistant', content=example_briefing().model_dump_json()))],
            usage=dict(prompt_tokens=10, completion_tokens=10, total_tokens=20)))
    crew = groq_crew()
    llm = crew.agents[0].llm
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='groq-test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        result = llm.call([dict(role='user', content='Return a briefing as JSON.')], response_model=Briefing)
    request, payload = captured[0]
    assert str(request.url) == 'https://api.groq.com/openai/v1/chat/completions'
    assert request.headers['authorization'] == 'Bearer groq-test-only'
    assert payload['model'] == 'openai/gpt-oss-120b'
    assert payload['response_format'] == {'type': 'json_object'}
    assert 'tools' not in payload
    assert payload.get('max_completion_tokens', payload.get('max_tokens')) == 4000
    assert 'request_deadline' not in payload
    assert llm.supports_function_calling()
    assert isinstance(result, Briefing)
    assert result.priorities[0].record_id == 'INC-001'


def test_groq_native_tool_roundtrip_keeps_structured_output_separate():
    captured = []
    tools = BusinessTools(load_dataset())
    crew = build_crew(tools, Settings('groq', 'openai/gpt-oss-120b',
        'groq-test-only', 'https://api.groq.com/openai/v1'), [], 'Brief me')
    def respond(request):
        body = json.loads(request.content)
        captured.append(body)
        finish = 'stop'
        if len(captured) == 1:
            finish = 'tool_calls'
            message = dict(role='assistant', content=None, tool_calls=[dict(id='mock-tool-call', type='function',
                function=dict(name='get_business_updates', arguments='{"category":"","status":""}'))])
        elif 'Chief of Staff' in json.dumps(body['messages']):
            message = dict(role='assistant', content=example_briefing().model_dump_json())
        else:
            message = dict(role='assistant', content=json.dumps(dict(findings=[dict(record_id='INC-001',
                source_ids=['INC-001', 'CON-001'], observation='Integration remains unavailable.')], limitations=[])))
        return httpx.Response(200, json=dict(id='mock-groq', object='chat.completion', created=0,
            model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason=finish, message=message)],
            usage=dict(prompt_tokens=10, completion_tokens=10, total_tokens=20)))
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        client = OpenAI(api_key='groq-test-only', base_url='https://api.groq.com/openai/v1', http_client=http, max_retries=0)
        for agent in crew.agents:
            agent.llm._client = client
        output = crew.kickoff()
    assert output.pydantic.priorities[0].record_id == 'INC-001'
    assert any(e.tool == 'get_business_updates' and e.actor == 'Business Operations Analyst' for e in tools.events)
    assert captured[0]['tools']
    assert all('properties' in tool['function']['parameters'] for tool in captured[0]['tools'])
    empty_parameters = [tool['function']['parameters'] for tool in captured[0]['tools']
        if not tool['function']['parameters']['properties']]
    assert empty_parameters
    assert all('required' not in parameters for parameters in empty_parameters)
    assert captured[0]['parallel_tool_calls'] is False
    assert all(not (body.get('tools') and body.get('response_format')) for body in captured)
    assert 'tools' not in captured[1]
    assert captured[1]['response_format'] == {'type': 'json_object'}
    assert '"title": "Analysis"' in captured[1]['messages'][-1]['content']
    assert all(body['model'] == 'openai/gpt-oss-120b' for body in captured)


def test_groq_honors_retry_after_header(monkeypatch):
    from crewai.llms.retry import run_with_rate_limit_retry
    delays = []
    monkeypatch.setattr('crewai.llms.base_llm.run_with_rate_limit_retry',
        lambda operation: run_with_rate_limit_retry(operation, sleep=delays.append))
    attempts = []
    def respond(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, headers={'retry-after': '12'}, json={'error':
                {'message': 'Rate limit', 'type': 'tokens', 'code': 'rate_limit_exceeded'}})
        return httpx.Response(200, json=dict(id='mock-groq', object='chat.completion', created=0,
            model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason='stop',
            message=dict(role='assistant', content='Recovered'))]))
    llm = groq_crew().agents[0].llm
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='groq-test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        assert llm.call([dict(role='user', content='Test retry behavior.')]) == 'Recovered'
    assert len(attempts) == 2
    assert delays == [13]


def test_groq_long_cooldown_stops_before_sleep_or_another_http_request(monkeypatch):
    from crewai.llms.retry import run_with_rate_limit_retry
    delays, attempts = [], []
    monkeypatch.setattr('crewai.llms.base_llm.run_with_rate_limit_retry',
        lambda operation: run_with_rate_limit_retry(operation, sleep=delays.append))
    def respond(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, headers={'retry-after': '654'}, json={'error':
                {'message': 'SECRET provider details', 'type': 'tokens', 'code': 'rate_limit_exceeded'}})
        return httpx.Response(200, json=dict(id='mock-groq', object='chat.completion', created=0,
            model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason='stop',
            message=dict(role='assistant', content='Recovered'))]))
    llm = groq_crew().agents[0].llm
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='groq-test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        with pytest.raises(RuntimeError, match='cooldown') as error:
            llm.call([dict(role='user', content='Brief me')])
    assert 'SECRET' not in str(error.value)
    assert error.value.__context__ is None
    assert len(attempts) == 1
    assert delays == []


@pytest.mark.parametrize('remaining', [0, 5])
def test_groq_run_budget_prevents_expired_requests_and_long_retry_waits(monkeypatch, remaining):
    from crewai.llms.retry import run_with_rate_limit_retry
    import praxis.agents.groq as adapter
    now = [100.0]
    attempts, delays = [], []
    llm = groq_crew().agents[0].llm.model_copy(update={'request_deadline': now[0] + remaining})
    monkeypatch.setattr(adapter, 'monotonic', lambda: now[0], raising=False)
    def sleep(delay):
        delays.append(delay)
        now[0] += delay
    monkeypatch.setattr('crewai.llms.base_llm.run_with_rate_limit_retry',
        lambda operation: run_with_rate_limit_retry(operation, sleep=sleep))
    def respond(request):
        attempts.append(request)
        if len(attempts) == 1 and remaining:
            return httpx.Response(429, headers={'retry-after': '10'}, json={'error':
                {'message': 'Quota', 'code': 'rate_limit_exceeded'}})
        return httpx.Response(200, json=dict(id='mock-groq', object='chat.completion', created=0,
            model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason='stop',
            message=dict(role='assistant', content='Recovered'))]))
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        with pytest.raises((TimeoutError, RuntimeError)):
            llm.call([dict(role='user', content='Brief me')])
    assert delays == []
    assert len(attempts) == (1 if remaining else 0)
    if attempts:
        assert attempts[0].extensions['timeout']['read'] <= remaining


@pytest.mark.parametrize('valid', [True, False])
def test_groq_json_mode_keeps_local_schema_validation(valid):
    captured = []
    def respond(request):
        body = json.loads(request.content)
        captured.append(body)
        content = example_briefing().model_dump_json() if valid else '{"executive_summary":"Missing required priorities"}'
        return httpx.Response(200, json=dict(id='mock-recovery', object='chat.completion', created=0,
            model='openai/gpt-oss-120b', choices=[dict(index=0, finish_reason='stop',
            message=dict(role='assistant', content=content))]))
    llm = groq_crew().agents[0].llm
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='groq-test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        if valid:
            result = llm.call([dict(role='user', content='Return a JSON briefing.')], response_model=Briefing)
            assert isinstance(result, Briefing)
        else:
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                llm.call([dict(role='user', content='Return a JSON briefing.')], response_model=Briefing)
    assert len(captured) == 1
    assert captured[0]['response_format'] == {'type': 'json_object'}
    assert 'tools' not in captured[0]
    assert 'source_ids' in captured[0]['messages'][-1]['content']


def test_groq_other_bad_requests_are_not_retried():
    import pytest
    from openai import BadRequestError
    attempts = []
    def respond(request):
        attempts.append(request)
        return httpx.Response(400, json={'error': {'message': 'Unsupported parameter', 'code': 'invalid_request_error'}})
    llm = groq_crew().agents[0].llm
    with httpx.Client(transport=httpx.MockTransport(respond)) as http:
        llm._client = OpenAI(api_key='groq-test-only', base_url=llm.base_url, http_client=http, max_retries=0)
        with pytest.raises(BadRequestError):
            llm.call([dict(role='user', content='Return JSON.')], response_model=Briefing)
    assert len(attempts) == 1
