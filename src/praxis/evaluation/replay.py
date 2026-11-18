"""Exercise real service/tools/validation with explicitly scripted crew outputs."""
import json
from types import SimpleNamespace
from unittest.mock import patch
from praxis.config import Settings
from praxis.schemas import Analysis, Briefing, Event
from praxis.tools import BusinessTools
from praxis.validation import OutputRejected, validate_analysis, validate_briefing
from praxis.services import briefing as service
from praxis.services.errors import ProviderCooldown
from .scoring import TOOL_MODELS
from .suite import Suite, Case, candidate, case_data


class ToolFailure(RuntimeError):
    pass


def empty_observation(origin):
    return dict(origin=origin, status='failed', released=False, candidate_present=False,
        analysis=None, briefing=None, metrics=None, calls=[], events=[], error_kind=None)


def invoke(business, name, arguments, observation, malformed=False):
    call = dict(name=name, arguments=arguments, status='error', result=None)
    observation['calls'].append(call)
    if name not in TOOL_MODELS:
        raise ValueError('Only read-only business tools are allowed')
    result = getattr(business, name)(**arguments)
    if malformed:
        call['result'] = {'malformed': True}
        raise ToolFailure('Malformed tool result')
    call.update(status='ok', result=result.model_dump(mode='json'))
    return result


def offline_case(suite: Suite, case: Case):
    obs = empty_observation('hand_authored_replay')
    data = case_data(suite, case)
    business = BusinessTools(data)
    if case.scope == 'tool':
        try:
            for call in case.calls:
                invoke(business, call['name'], call.get('arguments', {}), obs)
            obs['status'] = 'accepted'
        except (ValueError, TypeError):
            obs.update(status='rejected', error_kind='tool_input')
        obs['events'] = [e.model_dump(mode='json') for e in business.events]
        return obs
    raw = candidate(suite, case)

    class RecordedCrew:
        def __init__(self, tools):
            self.business = tools
            self.tasks = [SimpleNamespace(output=None)]

        def kickoff(self):
            tools = self.business
            if case.failure == 'timeout':
                raise TimeoutError('Injected timeout')
            if case.failure == 'interrupted':
                raise InterruptedError('Injected interrupted request')
            if case.failure == 'cooldown':
                raise ProviderCooldown(120)
            if case.failure == 'rate_limit':
                error = RuntimeError('Injected rate limit')
                error.status_code = 429
                raise error
            tools.actor = 'Business Operations Analyst'
            if case.failure == 'tool_failure':
                obs['calls'].append(dict(name='get_operating_snapshot', arguments={}, status='error', result=None))
                raise ToolFailure('Injected retrieval failure')
            for call in case.calls:
                invoke(tools, call['name'], call.get('arguments', {}), obs,
                    malformed=case.failure == 'malformed_tool')
            obs.update(candidate_present=True, analysis=raw.get('analysis'))
            analysis = Analysis.model_validate(raw.get('analysis'))
            validate_analysis(analysis, tools)
            tools.events.append(Event(actor=tools.actor, kind='task', detail='Scripted analysis validated'))
            self.tasks[0].output = SimpleNamespace(pydantic=analysis, raw=analysis.model_dump_json())
            tools.actor = 'Chief of Staff'
            if case.failure == 'chief_timeout':
                raise TimeoutError('Injected second-agent timeout')
            obs['briefing'] = raw.get('briefing')
            briefing = Briefing.model_validate(raw.get('briefing'))
            validate_briefing(briefing, tools, analysis)
            tools.events.append(Event(actor=tools.actor, kind='task', detail='Scripted briefing validated'))
            return SimpleNamespace(pydantic=briefing, raw=briefing.model_dump_json())

    def build(tools, *_):
        obs['metrics'] = tools.calculate_business_metrics().model_dump(mode='json')
        return RecordedCrew(tools)

    with patch.object(service, 'build_crew', build):
        try:
            result = service.run_briefing(case.question, data, Settings('openai', 'offline-scripted', 'not-a-key'))
            obs.update(status='accepted', released=True, events=[e.model_dump(mode='json') for e in result.events])
        except service.BriefingFailed as error:
            obs['events'] = [e.model_dump(mode='json') for e in error.events]
            obs['error_kind'] = classify_error(str(error), obs['events'])
            obs['status'] = 'rejected' if obs['error_kind'] == 'validation' else 'failed'
    return obs


def classify_error(message, events):
    details = message + ' ' + ' '.join(e.get('detail', '') for e in events if e.get('kind') == 'error')
    for tokens, kind in [(['ProviderCooldown', 'cooldown'], 'cooldown'),
            (['RateLimitError', 'rate limit'], 'rate_limit'),
            (['TimeoutError', 'APITimeoutError', 'ReadTimeout', 'timed out'], 'timeout'),
            (['InterruptedError'], 'interrupted'), (['ToolFailure'], 'tool_failure'),
            (['AuthenticationError'], 'authentication'),
            (['OutputRejected', 'ValidationError'], 'validation')]:
        if any(t in details for t in tokens):
            return kind
    return 'provider_or_runtime'
