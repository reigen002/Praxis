"""Local HTTP seam for the React desktop demo. No external action endpoints."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import Field, field_validator
from praxis.config import settings
from praxis.data import load_dataset, DEMO_DATASETS, DATASET_NAMES, YFS_PROFILE
from praxis.decisions import RulesProvider, get_provider
from praxis.decisions.jev import JevError
from praxis.schemas import Model
from praxis.services.briefing import BriefingFailed, run_briefing
from praxis.services.saved_runs import load_runs, save_run
from praxis.tools import BusinessTools

ROOT = Path(__file__).resolve().parents[2]
SAVED_RUNS = ROOT / 'artifacts' / 'saved-briefings'
DATASETS = DEMO_DATASETS
app = FastAPI(title='Praxis local API', version='0.2.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='praxis')
_jobs: dict[str, dict] = {}
_lock = Lock()


def business_for(dataset: str) -> BusinessTools:
    path = DATASETS.get(dataset)
    if path is None or not path.is_file():
        raise HTTPException(404, 'Unknown dataset')
    return BusinessTools(load_dataset(path))


def readiness(business: BusinessTools):
    config = settings()
    jev_ready = bool(os.getenv('JEV_API_KEY'))
    cached = None
    if jev_ready:
        try:
            provider = get_provider('jev', business)
            selected = config.jev_record_id or 'INC-001'
            if selected in business.by_id and hasattr(provider, 'get_cached'):
                cached = provider.get_cached(business.by_id[selected])
        except (ValueError, RuntimeError):
            pass
    return {'llm': {'provider': config.provider, 'model': config.model, 'configured': config.ready},
        'jev': {'configured': jev_ready, 'model': 'jev-1.13', 'live_verified': cached is not None,
            'cached_record_id': cached.record_id if cached else None, 'max_records_per_run': 1}}


@app.get('/api/health')
def health():
    return {'status': 'ok', 'application': 'Praxis'}


@app.get('/api/overview')
def overview(dataset: str = 'yfs'):
    business = business_for(dataset)
    metrics = business.calculate_business_metrics()
    deadlines = business.get_deadline_risks()
    policy = business.get_policy_escalations()
    rules = RulesProvider(business)
    return {'dataset': dataset, 'label': business.dataset.label, 'reference_date': business.dataset.reference_date,
        'profile': YFS_PROFILE if dataset == 'yfs' else None,
        'datasets': [{'id': name, 'name': DATASET_NAMES[name]}
            for name, path in DATASETS.items() if path.is_file()],
        'records': [r.model_dump(mode='json') for r in business.dataset.records],
        'metrics': metrics.model_dump(mode='json'), 'deadlines': deadlines.model_dump(mode='json'),
        'policy': policy.model_dump(mode='json'), 'decisions': [rules.evaluate(r).model_dump(mode='json') for r in business.dataset.records],
        'readiness': readiness(business)}


@app.get('/api/records/{record_id}')
def record_details(record_id: str, dataset: str = 'yfs'):
    business = business_for(dataset)
    if record_id not in business.by_id:
        raise HTTPException(404, 'Unknown record')
    return business.get_record_details(record_id).model_dump(mode='json')


@app.get('/api/saved-runs')
def saved_runs(dataset: str = 'yfs'):
    saved, warnings = load_runs(business_for(dataset).dataset, SAVED_RUNS)
    return {'runs': [item.model_dump(mode='json') for item in saved], 'warnings': warnings}


class RunRequest(Model):
    question: str = Field(min_length=1, max_length=2000)
    dataset: str = 'yfs'
    decision_provider: str = Field(default='rules', pattern='^(rules|jev)$')
    jev_record_id: str | None = None

    @field_validator('question')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('Enter a founder question')
        return value


def perform_run(job_id, request, dataset, config):
    with _lock:
        _jobs[job_id].update(status='running', started_at=datetime.now(timezone.utc).isoformat())
    try:
        result = run_briefing(request.question, dataset, config)
    except BriefingFailed as error:
        with _lock:
            _jobs[job_id].update(status='failed', error=str(error), events=[e.model_dump(mode='json') for e in error.events])
    except Exception:
        with _lock:
            _jobs[job_id].update(status='failed', error='The run could not complete. Check provider configuration and retry.', events=[])
    else:
        save_warning = None
        try:
            save_run(dataset, result, SAVED_RUNS)
        except (OSError, ValueError, TypeError):
            # An accepted live answer remains usable if local storage is unavailable.
            save_warning = 'This briefing completed but could not be saved for later. Export it before refreshing.'
        with _lock:
            _jobs[job_id].update(status='completed', result=result.model_dump(mode='json'), save_warning=save_warning)
    finally:
        with _lock:
            _jobs[job_id]['finished_at'] = datetime.now(timezone.utc).isoformat()


@app.post('/api/runs', status_code=202)
def start_run(request: RunRequest):
    business = business_for(request.dataset)
    config = settings()
    if not config.ready:
        raise HTTPException(503, 'LLM credentials are missing. Add them to .env and restart the API.')
    if request.jev_record_id and request.jev_record_id not in business.by_id:
        raise HTTPException(404, 'Unknown JEV target record')
    if request.decision_provider == 'jev' and not os.getenv('JEV_API_KEY'):
        raise HTTPException(503, 'JEV_API_KEY is missing. Choose rules or configure JEV privately.')
    config = replace(config, decision_provider=request.decision_provider, jev_record_id=request.jev_record_id)
    with _lock:
        if any(job['status'] in ('queued', 'running') for job in _jobs.values()):
            raise HTTPException(409, 'A briefing is already running. Wait for it to finish before starting another.')
        while len(_jobs) >= 20:
            oldest = next(iter(_jobs))
            del _jobs[oldest]
        job_id = str(uuid4())
        job = {'id': job_id, 'status': 'queued', 'created_at': datetime.now(timezone.utc).isoformat(),
            'question': request.question, 'dataset': request.dataset, 'decision_provider': request.decision_provider,
            'result': None, 'error': None, 'events': []}
        _jobs[job_id] = job
    _executor.submit(perform_run, job_id, request, business.dataset, config)
    return job


@app.get('/api/runs/{job_id}')
def run_status(job_id: str):
    with _lock:
        if job_id not in _jobs:
            raise HTTPException(404, 'Run not found; the local server may have restarted.')
        return dict(_jobs[job_id])


class DecisionRequest(Model):
    dataset: str = 'yfs'
    record_id: str = 'INC-001'


@app.get('/api/decisions/cached')
def cached_decision(dataset: str = 'demo', record_id: str = 'INC-001'):
    business = business_for(dataset)
    if record_id not in business.by_id:
        raise HTTPException(404, 'Unknown record')
    settings()
    try:
        cached = get_provider('jev', business).get_cached(business.by_id[record_id])
    except JevError as error:
        raise HTTPException(502, str(error)) from None
    except (ValueError, RuntimeError):
        raise HTTPException(503, 'The saved JEV decision is unavailable. No evaluation was requested.') from None
    if cached is None:
        raise HTTPException(404, 'No matching saved JEV decision. No evaluation was requested.')
    baseline = RulesProvider(business).evaluate(business.by_id[record_id])
    return {'baseline': baseline.model_dump(mode='json'), 'jev': cached.model_dump(mode='json'), 'cached': True}


@app.post('/api/decisions/evaluate')
def evaluate_decision(request: DecisionRequest):
    business = business_for(request.dataset)
    if request.record_id not in business.by_id:
        raise HTTPException(404, 'Unknown record')
    settings()
    baseline = RulesProvider(business).evaluate(business.by_id[request.record_id])
    try:
        provider = get_provider('jev', business)
        if hasattr(provider, 'get_cached'):
            cached = provider.get_cached(business.by_id[request.record_id])
            if cached:
                return {'baseline': baseline.model_dump(mode='json'), 'jev': cached.model_dump(mode='json'), 'cached': True}
        decision = provider.evaluate(business.by_id[request.record_id])
    except JevError as error:
        raise HTTPException(502, str(error)) from None
    except (ValueError, RuntimeError):
        raise HTTPException(502, 'JEV is unavailable or its result failed validation. No rules fallback was substituted.') from None
    return {'baseline': baseline.model_dump(mode='json'), 'jev': decision.model_dump(mode='json'),
        'cached': getattr(decision, 'cache_hit', False)}


FRONTEND = ROOT / 'frontend/dist'
if FRONTEND.is_dir():
    app.mount('/', StaticFiles(directory=FRONTEND, html=True), name='frontend')
