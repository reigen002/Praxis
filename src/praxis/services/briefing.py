import contextlib
import io
import time
from uuid import uuid4
from praxis.config import Settings, settings
from praxis.data import load_dataset
from praxis.decisions import RulesProvider, get_provider
from praxis.decisions.jev import JevError
from praxis.schemas import Analysis, Briefing, Dataset, Event, RunResult
from praxis.tools import BusinessTools
from praxis.validation import validate_analysis, validate_briefing
from praxis.services.errors import ProviderCooldown


class BriefingFailed(RuntimeError):
    def __init__(self, message, events=None):
        super().__init__(message)
        self.events = events or []


def build_crew(*args, **kwargs):
    # Delay heavy CrewAI imports until a live run is requested.
    from praxis.agents import build_crew as build
    return build(*args, **kwargs)


def run_briefing(question: str, dataset: Dataset | None = None, config: Settings | None = None) -> RunResult:
    start = time.monotonic()
    if not question.strip() or len(question) > 2000:
        raise BriefingFailed('Enter a founder question between one and two thousand characters.')
    config = config or settings()
    if not config.ready:
        raise BriefingFailed('Missing LLM credentials. Configure .env and restart. No agent run occurred.')
    business = BusinessTools(dataset or load_dataset())
    metrics = business.calculate_business_metrics()
    decision_scope = ''
    try:
        provider = get_provider(config.decision_provider, business)
        if config.decision_provider == 'jev':
            mandatory = business.get_policy_escalations().escalations
            target_id = getattr(config, 'jev_record_id', None) or (
                mandatory[0].record_id if mandatory else business.dataset.records[0].record_id)
            if target_id not in business.by_id:
                raise JevError('The selected JEV record does not exist; no paid request was made.', code='invalid_record')
            rules = RulesProvider(business)
            decisions = [(provider if r.record_id == target_id else rules).evaluate(r)
                for r in business.dataset.records]
            selected = next(d for d in decisions if d.record_id == target_id)
            decision_scope = (f'; JEV budget limited to selected record {target_id}'
                + (' (saved provider response reused)' if selected.cache_hit else ' (one decision request)')
                + '; all other records explicitly use rules-v1')
        else:
            decisions = [provider.evaluate(r) for r in business.dataset.records]
    except Exception as exc:
        message = str(exc) if isinstance(exc, JevError) else (
            'Missing JEV_API_KEY. Configure it to use JEV; no fallback occurred.'
            if config.decision_provider == 'jev' and isinstance(exc, ValueError)
            else 'Decision evaluation failed; no briefing was accepted.')
        business.events.append(Event(actor='Application', kind='error',
            detail=f'Decision evaluation failed ({type(exc).__name__}): {message}'))
        raise BriefingFailed(message, business.events) from None
    identities = sorted({d.provider + (f'/{d.model_version}' if d.model_version else '') for d in decisions})
    business.events.append(Event(actor='Application', kind='decision',
        detail='Evaluated with ' + ', '.join(identities) +
            ('; model probability estimates; mandatory policy remains authoritative' if any(d.probabilities is not None for d in decisions)
             else '; deterministic heuristic; no calibrated probabilities') + decision_scope,
        source_ids=[d.record_id for d in decisions]))
    try:
        # Suppress provider/library console bodies: errors may contain request headers.
        # Only our sanitized execution events are exposed to the UI.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            crew = build_crew(business, config, decisions, question)
            output = crew.kickoff()
        analysis_output = crew.tasks[0].output
        analysis = analysis_output.pydantic if isinstance(analysis_output.pydantic, Analysis) else Analysis.model_validate_json(analysis_output.raw)
        briefing = output.pydantic if isinstance(output.pydantic, Briefing) else Briefing.model_validate_json(output.raw)
        validate_analysis(analysis, business)
        validate_briefing(briefing, business, analysis)
    except Exception as exc:
        causes = []
        current = exc
        rate_limited = False
        timed_out = False
        cooldown = None
        seen = set()
        while current is not None and id(current) not in seen and len(causes) < 8:
            seen.add(id(current))
            rate_limited |= getattr(current, 'status_code', None) == 429
            timed_out |= isinstance(current, TimeoutError) or type(current).__name__ in ('APITimeoutError', 'ReadTimeout', 'ConnectTimeout')
            if isinstance(current, ProviderCooldown):
                cooldown = current
            causes.append(type(current).__name__ + (f' errno={current.errno}' if isinstance(current, OSError) else ''))
            current = current.__cause__ or current.__context__
        business.events.append(Event(actor='Application', kind='error', detail='Provider or output validation failed (' + ' > '.join(causes) + '); response withheld'))
        if cooldown:
            message = (f'Groq requested a cooldown of {cooldown.retry_after_seconds} seconds because its allowance is exhausted. '
                'The run stopped instead of waiting. Try after that interval or configure another available Groq model. No briefing was accepted.')
        elif rate_limited:
            message = 'The provider rate limit or quota was reached. Check your provider limits and wait before retrying. No briefing was accepted.'
        elif timed_out:
            message = 'The model request or agent task timed out. Check provider availability before retrying. No briefing was accepted.'
        else:
            message = 'The agent run failed or its output did not pass evidence checks. Check provider readiness, then retry. No briefing was accepted.'
        raise BriefingFailed(message, business.events) from None
    business.events.append(Event(actor='Application', kind='validation', detail='Final structure, source scope and escalation checks passed'))
    return RunResult(run_id=str(uuid4()), question=question, briefing=briefing, analysis=analysis,
        metrics=metrics, decisions=decisions, events=business.events, model=f'{config.provider}/{config.model}',
        elapsed_seconds=round(time.monotonic() - start, 2))
