"""Small evaluation runner: JSON labels, deterministic checks, explicit provenance."""
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import platform

from .suite import ROOT, Suite, Case, load_suite, digest
from .scoring import score_case, check
from .replay import offline_case

EVALUATOR_VERSION = '1.0.0'


def source_fingerprint(paths):
    value = ''.join(str(p.relative_to(ROOT)) + ':' + digest(p) for p in sorted(paths))
    return hashlib.sha256(value.encode()).hexdigest()


def summarize(cases):
    summary = {}
    names = sorted({name for c in cases for name in c['checks']})
    for name in names:
        checks = [c['checks'][name] for c in cases]
        summary[name] = check(sum(x['numerator'] for x in checks), sum(x['denominator'] for x in checks),
            'Micro aggregate over offered candidates/tool calls, including deliberately invalid candidates')
    attempted = [c for c in cases if c['observation']['status'] != 'not_run']
    positive = [c for c in attempted if c['expected_status'] == 'accepted' and 'workflow' in c['tags']]
    released = [c for c in cases if c['observation']['released']]
    summary['case_success'] = check(sum(c['passed'] for c in cases), len(cases), 'Expected disposition and required detections')
    summary['task_completion'] = check(sum(c['observation']['status'] == 'accepted' for c in positive), len(positive),
        'Positive workflow cases only; excludes deliberate rejection/outage cases')
    summary['timeout_rate'] = check(sum(c['observation'].get('error_kind') == 'timeout' for c in attempted),
        len(attempted), 'Injected timeouts in offline mode; lower is better')
    summary['released_policy_violations'] = check(sum(bool(c['released_violations']) for c in released),
        len(released), 'Released briefings with any hard-check failure; lower is better')
    for name in ('released_policy_violations', 'timeout_rate'):
        summary[name]['passed'] = summary[name]['numerator'] == 0 if summary[name]['denominator'] else None
    return summary


def make_report(suite, cases, mode, model):
    suite_hash = hashlib.sha256(suite.model_dump_json().encode()).hexdigest()
    prompts = [ROOT / 'src/praxis/agents/__init__.py', ROOT / 'src/praxis/agents/groq.py', ROOT / 'src/praxis/config.py']
    summary = summarize(cases)
    violations = sum(bool(c['released_violations']) for c in cases)
    failures = [c['id'] for c in cases if not c['passed']]
    gate = (violations <= suite.thresholds['max_released_policy_violations'] and
        summary['case_success']['value'] >= suite.thresholds['min_case_success_rate'])
    return dict(schema_version=1, evaluator_version=EVALUATOR_VERSION, mode=mode,
        model=model, decision_provider='rules', suite_version=suite.version, suite_sha256=suite_hash,
        run_date=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
        dependencies={name: version(name) for name in ('crewai', 'pydantic')},
        prompt_config_sha256=source_fingerprint(prompts),
        application_sha256=source_fingerprint((ROOT / 'src/praxis').rglob('*.py')),
        evaluator_sha256=source_fingerprint((ROOT / 'src/praxis/evaluation').rglob('*.py')),
        datasets={name: dict(sha256=label.sha256, reference_date=label.reference_date) for name, label in suite.datasets.items()},
        thresholds=suite.thresholds, gate_passed=gate, failing_cases=failures,
        provider_errors=[dict(case=c['id'], kind=c['observation']['error_kind']) for c in cases
            if c['observation'].get('error_kind') not in (None, 'validation', 'tool_input')],
        summary=summary, cases=cases,
        limitations=['Offline replay evaluates contracts and guardrails, not model answer accuracy.',
            'Citations are label/membership checks, not semantic entailment.',
            'Keyword and action-claim checks are narrow and can miss paraphrases.',
            'No LLM judge. No live provider calls or JEV in offline mode.',
            'Offline durations/usage are not model performance measurements.'])


def run_suite(suite: Suite, case_ids=None):
    selected = select_cases(suite, case_ids)
    results = [score_case(suite, c, offline_case(suite, c)) for c in selected]
    return make_report(suite, results, 'offline', 'hand-authored/scripted-v1')


def select_cases(suite, case_ids):
    requested = set(case_ids or [c.id for c in suite.cases])
    if requested - {c.id for c in suite.cases}:
        raise ValueError('Unknown evaluation case ID')
    return [c for c in suite.cases if c.id in requested]


def compare_reports(baseline, updated):
    if (baseline['suite_sha256'] != updated['suite_sha256'] or baseline['mode'] != updated['mode'] or
            {c['id'] for c in baseline['cases']} != {c['id'] for c in updated['cases']} or
            baseline.get('evaluator_sha256') != updated.get('evaluator_sha256') or
            baseline['evaluator_version'] != updated['evaluator_version']):
        raise ValueError('Reports are not comparable: suite, mode, evaluator and case populations must match')
    before = {c['id']: c for c in baseline['cases']}
    after = {c['id']: c for c in updated['cases']}
    return {'baseline_application': baseline['application_sha256'], 'updated_application': updated['application_sha256'],
        'baseline_model': baseline['model'], 'updated_model': updated['model'],
        'new_failures': sorted(i for i in before if before[i]['passed'] and not after[i]['passed']),
        'resolved_failures': sorted(i for i in before if not before[i]['passed'] and after[i]['passed']),
        'deltas': {name: round(metric['value'] - baseline['summary'][name]['value'], 6)
            if metric['value'] is not None and baseline['summary'][name]['value'] is not None else None
            for name, metric in updated['summary'].items()},
        'note': 'Offline changes measure deterministic behavior on fixed candidates. Live deltas are observations, not causal proof.'}


def markdown(report):
    lines = ['# Praxis evaluation', '', f"Mode: **{report['mode']}**; model: `{report['model']}`; suite: `{report['suite_version']}`.",
        f"Gate: **{'PASS' if report['gate_passed'] else 'FAIL'}**. Run: {report['run_date']}", '',
        'Offline origin is `hand_authored_replay`; never live model output.', '',
        '| Measure | Numerator / denominator | Value |', '|---|---:|---:|']
    for name, m in report['summary'].items():
        lines.append(f"| {name} | {m['numerator']} / {m['denominator']} | {m['value'] if m['value'] is not None else 'N/A'} |")
    lines += ['', 'Candidate measures include deliberately invalid outputs. Case success measures correct disposition.', '',
        '| Case | Expected → observed | Verdict / reason |', '|---|---|---|']
    for c in report['cases']:
        reason = '; '.join(c['reasons']) or 'Expected behavior; required checks satisfied'
        lines.append(f"| {c['id']} | {c['expected_status']} → {c['observation']['status']} | {'PASS' if c['passed'] else 'FAIL'}: {reason} |")
    if 'comparison' in report:
        lines += ['', '## Comparison', '', '```json', json.dumps(report['comparison'], indent=2), '```']
    lines += ['', '## Limits', '', *['- ' + s for s in report['limitations']], '']
    return '\n'.join(lines)
