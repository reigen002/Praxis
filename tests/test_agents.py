import os
from types import SimpleNamespace
import pytest
from praxis.config import Settings
from praxis.data import load_dataset
from praxis.tools import BusinessTools
from praxis.agents import build_crew
from praxis.services.briefing import run_briefing, BriefingFailed


def test_real_crewai_configuration_and_tool_invocation():
    from crewai import Process
    tools = BusinessTools(load_dataset())
    crew = build_crew(tools, Settings('openai', 'gpt-4.1-mini', 'test-key'), [], 'Brief me')
    assert len(crew.agents) == 2
    assert crew.process == Process.sequential
    assert crew.tasks[1].context == [crew.tasks[0]]
    assert crew.tasks[0].output_pydantic is not None
    tools.actor = 'Business Operations Analyst'
    retrieval = next(t for t in crew.agents[0].tools if t.name == 'get_record_details')
    result = retrieval.run(record_id='INC-001')
    assert 'CON-001' in result
    assert tools.events[-1].source_ids == ['INC-001', 'CON-001', 'NOTE-001', 'NOTE-002']


@pytest.mark.parametrize('record_id', ['INC-001', 'OPS-001'])
def test_analyst_handoff_requires_mandatory_incident_and_contract_evidence(record_id):
    from praxis.schemas import Analysis
    business = BusinessTools(load_dataset('data/synthetic/yfs_operations.json'))
    crew = build_crew(business, Settings('openai', 'gpt-4.1-mini', 'test-key'), [], 'Brief me')
    business.get_business_updates()
    incomplete = Analysis(findings=[dict(record_id=record_id, source_ids=[record_id],
        observation='Programme readiness requires attention.')])
    accepted, feedback = crew.tasks[0].guardrail(SimpleNamespace(pydantic=incomplete))
    assert not accepted
    assert 'INC-001' in feedback and 'CON-001' in feedback
    complete = Analysis(findings=[dict(record_id='INC-001', source_ids=['INC-001', 'CON-001'],
        observation='The unresolved incident may affect the partner renewal.')])
    assert crew.tasks[0].guardrail(SimpleNamespace(pydantic=complete))[0]


def test_provider_failure_is_sanitized(monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError('SECRET-auth-token provider response')
    monkeypatch.setattr('praxis.services.briefing.build_crew', fail)
    with pytest.raises(BriefingFailed) as error:
        run_briefing('Brief me', config=Settings('openai', 'test', 'secret'))
    assert 'SECRET' not in str(error.value)
    assert 'secret' not in str(error.value)
    assert error.value.events[-1].kind == 'error'
    assert 'timed out' in str(error.value).lower()


def test_missing_credentials_fail_without_fallback():
    with pytest.raises(BriefingFailed, match='credential'):
        run_briefing('Brief me', config=Settings('openai', 'test', ''))


def test_rate_limit_is_actionable_without_leaking_response(monkeypatch):
    import httpx
    from openai import RateLimitError
    def fail(*args, **kwargs):
        raise RateLimitError('secret provider body', response=httpx.Response(429,
            request=httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')), body=None)
    monkeypatch.setattr('praxis.services.briefing.build_crew', fail)
    with pytest.raises(BriefingFailed, match='rate limit') as error:
        run_briefing('Brief me', config=Settings('groq', 'openai/gpt-oss-120b', 'test-only'))
    assert 'secret' not in str(error.value)


def test_provider_cooldown_survives_agent_wrapper_with_actionable_error(monkeypatch):
    from praxis.services.errors import ProviderCooldown
    def fail(*args, **kwargs):
        try:
            raise ProviderCooldown(654)
        except ProviderCooldown as cause:
            raise RuntimeError('SECRET agent wrapper') from cause
    monkeypatch.setattr('praxis.services.briefing.build_crew', fail)
    with pytest.raises(BriefingFailed, match='654 seconds') as error:
        run_briefing('Brief me', config=Settings('groq', 'test', 'secret'))
    assert 'SECRET' not in str(error.value)
    assert 'stopped instead of waiting' in str(error.value)


def test_anthropic_gateway_model_alias_uses_native_provider():
    from crewai.llms.providers.anthropic.completion import AnthropicCompletion
    crew = build_crew(BusinessTools(load_dataset()),
        Settings('anthropic', 'gateway-model-alias', 'test-key', 'http://localhost:20128'), [], 'Brief me')
    assert isinstance(crew.agents[0].llm, AnthropicCompletion)
    assert crew.agents[0].llm.model == 'gateway-model-alias'


@pytest.mark.live
@pytest.mark.parametrize('scenario,question', [
    ('morning', 'Prepare my founder briefing for today. What are the three most important issues, and why?'),
    ('explanation', 'Why is the customer renewal issue more urgent than the feature request?')])
def test_live_crew(scenario, question):
    from pathlib import Path
    try:
        result = run_briefing(question)
    except BriefingFailed as exc:
        import json
        Path('artifacts').mkdir(exist_ok=True)
        Path(f'artifacts/live-{scenario}-failed-events.json').write_text(
            json.dumps([e.model_dump(mode='json') for e in exc.events], indent=2), encoding='utf-8')
        pytest.fail(str(exc) + '\n' + '\n'.join(e.detail for e in exc.events if e.kind in ('validation', 'task', 'error')), pytrace=False)
    assert result.mode == 'live'
    assert any(e.actor == 'Business Operations Analyst' and e.tool == 'get_business_updates' for e in result.events)
    assert result.briefing.priorities[0].record_id == 'INC-001'
    assert len(result.briefing.priorities) == 3
    assert result.briefing.follow_ups
    path = Path('artifacts')
    path.mkdir(exist_ok=True)
    (path / f'live-{scenario}.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
