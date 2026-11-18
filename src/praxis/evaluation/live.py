"""Opt-in live calls isolated in killable child processes. JEV is always disabled."""
from dataclasses import replace
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .suite import case_data
from .scoring import score_case
from .replay import empty_observation, classify_error


def bounded_worker(command, timeout):
    # A process, rather than a future/thread timeout, terminates blocked SDK calls.
    with subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as process:
        try:
            process.wait(timeout=timeout)
            return process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return 'timeout'
        except KeyboardInterrupt:
            process.kill()
            process.wait()
            raise


def worker(input_path, output_path):
    from praxis.config import settings
    from praxis.schemas import Dataset
    from praxis.services.briefing import run_briefing, BriefingFailed
    payload = json.loads(Path(input_path).read_text())
    config = replace(settings(), decision_provider='rules', jev_record_id=None)
    obs = empty_observation('live_provider')
    obs['model'] = config.provider + '/' + config.model
    start = time.monotonic()
    try:
        # Includes configuration/SDK output suppression; never persist raw exceptions.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = run_briefing(payload['question'], Dataset.model_validate(payload['dataset']), config)
        obs.update(status='accepted', released=True, candidate_present=True,
            analysis=result.analysis.model_dump(mode='json'), briefing=result.briefing.model_dump(mode='json'),
            metrics=result.metrics.model_dump(mode='json'), events=[e.model_dump(mode='json') for e in result.events])
        # The application records successful tool events but not raw arguments/results.
        # Do not manufacture them or claim full live tool-contract observability.
    except BriefingFailed as error:
        obs['events'] = [e.model_dump(mode='json') for e in error.events]
        obs['error_kind'] = classify_error(str(error), obs['events'])
        obs['status'] = 'rejected' if obs['error_kind'] == 'validation' else 'failed'
    except Exception:
        obs['error_kind'] = 'provider_or_runtime'
    obs['elapsed_seconds'] = round(time.monotonic() - start, 3)
    content = json.dumps(obs, ensure_ascii=False)
    secrets = [config.api_key, *[v for k, v in os.environ.items() if
        k.endswith(('_API_KEY', '_AUTH_TOKEN')) and len(v) > 6]]
    for secret in secrets:
        if secret:
            content = content.replace(secret, '<REDACTED>')
    Path(output_path).write_text(content, encoding='utf-8')


def run_live(suite, selected, timeout, max_cases):
    from . import make_report
    if not selected or len(selected) > max_cases or any(not c.live_eligible for c in selected):
        raise ValueError('Select named live-eligible cases within --max-live-cases')
    results, stopped, interrupted = [], False, False
    model = 'not_observed'
    for case in selected:
        obs = empty_observation('live_provider')
        if stopped:
            obs.update(status='not_run', error_kind='prior_failure')
        else:
            with tempfile.TemporaryDirectory(prefix='praxis-eval-') as tmp:
                source, target = Path(tmp) / 'input.json', Path(tmp) / 'output.json'
                source.write_text(json.dumps({'dataset': case_data(suite, case).model_dump(mode='json'),
                    'question': case.question}), encoding='utf-8')
                try:
                    status = bounded_worker([sys.executable, '-m', 'praxis.evaluation',
                        '--allow-live', '--worker', str(source), str(target)], timeout)
                    if status == 'timeout':
                        obs['error_kind'] = 'timeout'
                    elif status != 0 or not target.is_file():
                        obs['error_kind'] = 'worker_failure'
                    else:
                        obs = json.loads(target.read_text(encoding='utf-8'))
                        model = obs.pop('model', model)
                except KeyboardInterrupt:
                    obs['error_kind'] = 'interrupted'
                    interrupted = True
                stopped = obs['status'] != 'accepted'
        results.append(score_case(suite, case, obs))
    report = make_report(suite, results, 'live', model)
    report['interrupted'] = interrupted
    report['limitations'] = [s for s in report['limitations'] if not s.startswith('No live')]
    report['limitations'].append('Live tool traces expose names/source IDs, not arguments or raw results; full tool-contract checks are N/A. API usage/cost is unobserved.')
    return report
