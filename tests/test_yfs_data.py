"""Research-informed synthetic education operations; no actual YFS records."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import json
import httpx
from fastapi.testclient import TestClient
from praxis.api import app
from praxis.data import load_dataset
from praxis.decisions import RulesProvider
from praxis.decisions.jev import JevProvider
from praxis.tools import BusinessTools

YFS_PATH = Path('data/synthetic/yfs_operations.json')


def test_school_seed_is_synthetic_coherent_and_covers_programme_operations():
    dataset = load_dataset(YFS_PATH)
    assert dataset.label == 'SYNTHETIC DEMONSTRATION DATA'
    assert dataset.reference_date == date(2026, 10, 30)
    assert len(dataset.records) == 28
    content = ' '.join(row.title + ' ' + row.description for row in dataset.records).lower()
    for topic in ('cohort', 'mentor', 'internship', 'school', 'sponsor', 'outcome', 'newsletter'):
        assert topic in content
    for row in dataset.records:
        assert row.created_at <= dataset.reference_date
        assert row.deadline is None or row.created_at <= row.deadline
        assert row.source.startswith('Synthetic ')
        assert '@' not in row.description
    assert {row.currency for row in dataset.records if row.contract_value is not None} == {'INR'}


def test_school_metrics_separate_signed_agreements_from_proposals_and_missing_values():
    tools = BusinessTools(load_dataset(YFS_PATH))
    metrics = tools.calculate_business_metrics()
    assert metrics.exposure_by_currency == {'INR': Decimal('300000')}
    assert metrics.pipeline_by_currency == {'INR': Decimal('340000')}
    assert metrics.open_issues == 13
    assert metrics.overdue_tasks == 3
    assert metrics.customer_escalations == 4
    assert metrics.opportunities_awaiting_action == 3
    assert metrics.missing_financial_ids == ['CAN-002', 'SALE-003']
    assert set(metrics.cohorts['exposure']) == {'CON-001', 'CON-002'}
    assert 'DONE-002' not in metrics.source_ids


def test_cohort_incident_is_mandatory_and_optional_redesign_is_routine():
    tools = BusinessTools(load_dataset(YFS_PATH))
    assert tools.get_policy_escalations().escalations[0].source_ids == ['INC-001', 'CON-001']
    rules = RulesProvider(tools)
    assert rules.evaluate(tools.by_id['INC-001']).urgency == 'Critical'
    assert rules.evaluate(tools.by_id['FEAT-001']).urgency == 'Routine'
    assert rules.evaluate(tools.by_id['DONE-001']).urgency == 'Routine'
    assert tools.by_id['FEAT-001'].deadline is None
    assert tools.by_id['NOTE-001'].description != tools.by_id['NOTE-002'].description


def test_school_labeled_routing_and_urgency_regression_fixture():
    tools = BusinessTools(load_dataset(YFS_PATH))
    rules = RulesProvider(tools)
    labels = json.loads(Path('data/synthetic/yfs_evaluation.json').read_text())
    assert len(labels) == 10
    for label in labels:
        result = rules.evaluate(tools.by_id[label['record_id']])
        assert result.classification == label['classification']
        assert result.urgency == label['urgency']


def test_api_defaults_to_school_demo_and_retains_startup_demo():
    client = TestClient(app)
    body = client.get('/api/overview').json()
    assert body['dataset'] == 'yfs'
    assert 'agreement' in body['profile']['exposure_label'].lower()
    assert 'partnership' in body['profile']['pipeline_label'].lower()
    assert 'fictional' in body['profile']['description'].lower()
    assert {item['id'] for item in body['datasets']} == {'yfs', 'demo', 'original'}
    old = client.get('/api/overview?dataset=demo').json()
    assert old['records'][0]['customer_or_team'] == 'Cedar Demo'
    assert Decimal(old['metrics']['exposure_by_currency']['USD']) == Decimal('84000')


def test_startup_jev_cache_cannot_be_presented_as_a_school_decision(tmp_path):
    from test_jev import response_body
    old_tools = BusinessTools(load_dataset('data/synthetic/founder_demo.json'))
    school_tools = BusinessTools(load_dataset(YFS_PATH))
    path = tmp_path / 'decisions.json'
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response_body()))) as client:
        old = JevProvider(old_tools, api_key='test-only', client=client, cache_path=path)
        old.evaluate(old_tools.by_id['INC-001'])
    school = JevProvider(school_tools, api_key='test-only', cache_path=path)
    assert school.get_cached(school_tools.by_id['INC-001']) is None
    assert old.get_cached(old_tools.by_id['INC-001']).cache_hit
