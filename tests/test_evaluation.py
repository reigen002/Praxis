"""Independent behavioral checks of the evaluation harness; never live calls."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'data/evaluation/v1/suite.json'


def evaluation():
    # A missing implementation is an explicit RED assertion, not collection failure.
    import importlib.util
    assert importlib.util.find_spec('praxis.evaluation'), 'Evaluation package is not implemented'
    from praxis.evaluation import load_suite, run_suite, compare_reports, score_case
    return load_suite, run_suite, compare_reports, score_case


def test_offline_runner_uses_real_validation_and_never_network(monkeypatch):
    load, run, _, _ = evaluation()
    import socket
    monkeypatch.setattr(socket.socket, 'connect', lambda *a: pytest.fail('Offline network access'))
    report = run(load(SUITE), case_ids=['yfs-morning'])
    assert report['mode'] == 'offline'
    assert report['cases'][0]['passed']
    assert report['cases'][0]['observation']['origin'] == 'hand_authored_replay'
    assert report['summary']['task_completion']['value'] == 1
    assert report['summary']['released_policy_violations']['numerator'] == 0
    assert report['summary']['released_policy_violations']['passed'] is True


@pytest.mark.parametrize('case_id,check', [
    ('unknown-source', 'source_id_validity'),
    ('citation-leakage', 'citation_precision'),
    ('prose-reference-leakage', 'prose_citation_scope'),
    ('schema-missing', 'structured_output_validity'),
    ('schema-extra', 'structured_output_validity'),
    ('numeric-hallucination', 'numeric_claim_correctness'),
    ('escalation-downgrade', 'mandatory_escalation_recall'),
    ('approval-bypass', 'unauthorized_action_safety'),
    ('injection-obeyed', 'injection_resistance'),
])
def test_adversarial_candidate_is_detected_even_when_safely_rejected(case_id, check):
    load, run, _, _ = evaluation()
    case = run(load(SUITE), case_ids=[case_id])['cases'][0]
    assert case['checks'][check]['passed'] is False
    assert case['observation']['status'] != 'accepted'
    assert case['passed'], case['reasons']


def test_incorrect_metrics_cannot_hide_behind_correct_prose():
    load, run, _, score = evaluation()
    suite = load(SUITE)
    case = suite.cases[0]
    report = run(suite, case_ids=[case.id])
    observation = copy.deepcopy(report['cases'][0]['observation'])
    observation['metrics']['exposure_by_currency']['INR'] = '999999.00'
    result = score(suite, case, observation)
    assert not result['checks']['numeric_claim_correctness']['passed']
    assert not result['passed']


def test_unsupported_amount_and_unknown_value_are_distinct():
    load, run, _, _ = evaluation()
    report = run(load(SUITE), case_ids=['missing-information', 'conflicting-evidence'])
    assert all(c['passed'] for c in report['cases'])
    assert all(c['checks']['answer_labels']['passed'] for c in report['cases'])


@pytest.mark.parametrize('case_id,error', [
    ('provider-timeout', 'timeout'), ('provider-rate-limit', 'rate_limit'),
    ('provider-cooldown', 'cooldown'), ('tool-failure', 'tool_failure'),
    ('malformed-tool-result', 'tool_failure'), ('chief-timeout', 'timeout'),
    ('interrupted-run', 'interrupted'),
])
def test_failures_are_not_accepted_and_have_typed_reports(case_id, error):
    load, run, _, _ = evaluation()
    case = run(load(SUITE), case_ids=[case_id])['cases'][0]
    assert case['passed'], case['reasons']
    assert case['observation']['status'] == 'failed'
    assert case['observation']['error_kind'] == error
    assert case['observation']['released'] is False


def test_comparison_refuses_different_suite_or_case_populations():
    load, run, compare, _ = evaluation()
    report = run(load(SUITE), case_ids=['yfs-morning'])
    assert compare(report, report)['new_failures'] == []
    changed = copy.deepcopy(report)
    changed['suite_sha256'] = 'different'
    with pytest.raises(ValueError, match='comparab'):
        compare(report, changed)
    changed = copy.deepcopy(report)
    changed['cases'] = []
    with pytest.raises(ValueError, match='comparab'):
        compare(report, changed)


def test_fixture_hash_and_duplicate_case_ids_fail_closed(tmp_path):
    load, _, _, _ = evaluation()
    raw = json.loads(SUITE.read_text())
    raw['cases'].append(raw['cases'][0])
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match='Duplicate'):
        load(path)
    raw['cases'].pop()
    raw['datasets']['yfs']['sha256'] = '0' * 64
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match='fingerprint'):
        load(path)


def test_live_requires_explicit_opt_in_before_loading_credentials():
    evaluation()
    result = subprocess.run([sys.executable, '-m', 'praxis.evaluation', '--mode', 'live'],
        cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2
    assert '--allow-live' in result.stderr


def test_cli_emits_json_and_readable_report(tmp_path):
    evaluation()
    out = tmp_path / 'run'
    result = subprocess.run([sys.executable, '-m', 'praxis.evaluation', '--case', 'yfs-morning',
        '--output', str(out)], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    report = json.loads(out.with_suffix('.json').read_text())
    assert report['cases'][0]['passed']
    assert 'hand_authored_replay' in out.with_suffix('.md').read_text()


@pytest.mark.parametrize('replacement', [None, 'INC-001', [{'bad': 'value'}], {'unexpected': []}])
def test_malformed_citations_produce_a_score_instead_of_crashing(replacement):
    load, run, _, score = evaluation()
    suite = load(SUITE)
    observation = run(suite, case_ids=['yfs-morning'])['cases'][0]['observation']
    observation['briefing']['priorities'][0]['source_ids'] = replacement
    result = score(suite, suite.cases[0], observation)
    assert result['checks']['structured_output_validity']['passed'] is False
    assert result['passed'] is False


def test_live_worker_cannot_bypass_opt_in():
    evaluation()
    result = subprocess.run([sys.executable, '-m', 'praxis.evaluation', '--worker', 'unused', 'unused'],
        cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2
    assert '--allow-live' in result.stderr


def test_process_deadline_kills_a_blocked_worker(tmp_path):
    evaluation()
    from praxis.evaluation.live import bounded_worker
    import time
    started = time.monotonic()
    result = bounded_worker([sys.executable, '-c', 'import time; time.sleep(60)'], timeout=0.1)
    assert result == 'timeout'
    assert time.monotonic() - started < 10


@pytest.mark.parametrize('method,args', [
    ('get_business_updates', {'category': 'invented'}),
    ('get_deadline_risks', {'window_days': 1.5}),
    ('get_deadline_risks', {'window_days': True}),
])
def test_invalid_tool_arguments_reject_at_shared_business_boundary(method, args):
    from praxis.data import load_dataset
    from praxis.tools import BusinessTools
    tools = BusinessTools(load_dataset())
    with pytest.raises(ValueError):
        getattr(tools, method)(**args)


@pytest.mark.parametrize('claim', ['I sent the email.', 'Praxis has already sent the message.',
    'We deleted the complaint.', 'The assistant transferred the funds.'])
def test_application_rejects_claimed_external_execution(claim):
    from praxis.validation import check_prose, OutputRejected
    with pytest.raises(OutputRejected, match='action'):
        check_prose(claim)


def test_application_keeps_proposed_action_and_local_review_available():
    from praxis.validation import check_prose
    check_prose('Draft an email for human approval. Please confirm learner access.')


def test_native_crewai_deadline_input_schema_rejects_bool():
    from praxis.agents import build_tools
    from praxis.data import load_dataset
    from praxis.tools import BusinessTools
    from pydantic import ValidationError
    tools = build_tools(BusinessTools(load_dataset()))
    deadline = next(t for t in tools if t.name == 'get_deadline_risks')
    with pytest.raises(ValidationError):
        deadline.args_schema.model_validate({'window_days': True})


def test_interrupted_live_session_writes_results_and_does_not_start_remaining_cases(monkeypatch):
    load, _, _, _ = evaluation()
    from praxis.evaluation.live import run_live
    import praxis.evaluation.live as live
    def interrupted(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr(live, 'bounded_worker', interrupted)
    suite = load(SUITE)
    report = run_live(suite, [suite.cases[0], suite.cases[1]], timeout=5, max_cases=2)
    assert report['interrupted']
    assert report['cases'][0]['observation']['error_kind'] == 'interrupted'
    assert report['cases'][1]['observation']['status'] == 'not_run'
    assert not report['gate_passed']


def test_offline_report_is_reproducible_apart_from_run_date():
    load, run, _, _ = evaluation()
    suite = load(SUITE)
    first, second = run(suite, ['yfs-morning']), run(suite, ['yfs-morning'])
    for report in (first, second):
        report.pop('run_date')
        for case in report['cases']:
            for event in case['observation']['events']:
                event.pop('timestamp')
    assert first == second


def test_source_membership_does_not_double_count_structural_ids_as_prose():
    load, run, _, score = evaluation()
    suite = load(SUITE)
    case = suite.cases[0]
    obs = run(suite, [case.id])['cases'][0]['observation']
    # Every primary/source field occurrence counts once, plus IDs actually in prose.
    raw = {'analysis': obs['analysis'], 'briefing': obs['briefing']}
    def count(node):
        if isinstance(node, list):
            return sum(count(x) for x in node)
        if isinstance(node, dict):
            return sum(1 if k == 'record_id' else len(v) if k == 'source_ids' else count(v) for k, v in node.items())
        import re
        return len(re.findall(r'\b[A-Z]+-\d{3,}\b', node)) if isinstance(node, str) else 0
    assert score(suite, case, obs)['checks']['source_id_validity']['denominator'] == count(raw)


def test_comparison_rejects_a_different_evaluator_implementation():
    load, run, compare, _ = evaluation()
    report = run(load(SUITE), ['yfs-morning'])
    other = copy.deepcopy(report)
    other['evaluator_sha256'] = 'different'
    with pytest.raises(ValueError, match='comparab'):
        compare(report, other)
