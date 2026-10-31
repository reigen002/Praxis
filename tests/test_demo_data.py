from datetime import date
from decimal import Decimal
from pathlib import Path

from praxis.data import load_dataset
from praxis.tools import BusinessTools


DEMO_PATH = Path(__file__).resolve().parents[1] / 'data' / 'synthetic' / 'founder_demo.json'


def test_demo_parses_with_coherent_dates_and_synthetic_sources():
    dataset = load_dataset(DEMO_PATH)
    assert dataset.label == 'SYNTHETIC DEMONSTRATION DATA'
    assert dataset.reference_date == date(2026, 10, 29)
    assert len(dataset.records) == 28
    for row in dataset.records:
        assert row.created_at <= dataset.reference_date
        assert row.deadline is None or row.created_at <= row.deadline
        assert 1 <= len(row.description) <= 2000
        assert row.source.startswith('Synthetic ')
    assert len({row.source for row in dataset.records}) >= 5


def test_demo_preserves_existing_identifiers_links_and_metric_eligibility():
    original = {row.record_id: row for row in load_dataset().records}
    demo = {row.record_id: row for row in load_dataset(DEMO_PATH).records}
    assert set(demo) == set(original)
    for record_id, row in demo.items():
        previous = original[record_id]
        assert (row.category, row.status, row.deadline, row.severity) == (
            previous.category, previous.status, previous.deadline, previous.severity)
        assert row.related_record_ids == previous.related_record_ids
        assert (row.contract_value, row.currency, row.contract_id) == (
            previous.contract_value, previous.currency, previous.contract_id)


def test_demo_metrics_keep_recorded_exposure_separate_from_potential_pipeline():
    tools = BusinessTools(load_dataset(DEMO_PATH))
    metrics = tools.calculate_business_metrics()
    assert metrics.exposure_by_currency == {'USD': Decimal('84000.00')}
    assert metrics.pipeline_by_currency == {'USD': Decimal('172000.00')}
    assert (metrics.open_issues, metrics.overdue_tasks, metrics.customer_escalations,
        metrics.opportunities_awaiting_action) == (11, 3, 4, 3)
    assert metrics.cohorts['exposure'] == ['CON-001', 'CON-002']
    assert set(metrics.cohorts['overdue_tasks']) == {'OPS-001', 'FIN-001', 'OPS-004'}
    assert metrics.missing_financial_ids == ['CAN-002']
    assert tools.by_id['CON-001'].contract_value == Decimal('48000.00')
    assert tools.by_id['CON-002'].contract_value == Decimal('36000.00')
    assert tools.by_id['SALE-001'].contract_value == Decimal('120000.00')
    assert tools.by_id['CAN-002'].contract_value is None


def test_demo_retains_mandatory_renewal_rule_and_optional_feature():
    tools = BusinessTools(load_dataset(DEMO_PATH))
    escalation, = tools.get_policy_escalations().escalations
    assert escalation.record_id == 'INC-001'
    assert escalation.rule == 'CRITICAL_SERVICE_RENEWAL'
    assert set(escalation.source_ids) == {'INC-001', 'CON-001'}
    deadlines = {risk.record_id: risk for risk in tools.get_deadline_risks().risks}
    assert deadlines['SALE-001'].days_remaining == 1
    assert tools.by_id['FEAT-001'].deadline is None
    assert 'FEAT-001' not in deadlines
    assert 'DONE-001' not in deadlines


def test_demo_preserves_contradictory_restoration_evidence_and_security_dependency():
    tools = BusinessTools(load_dataset(DEMO_PATH))
    evidence = tools.get_record_details('INC-001')
    assert set(evidence.source_ids) == {'INC-001', 'CON-001', 'NOTE-001', 'NOTE-002'}
    support, engineering = tools.by_id['NOTE-001'], tools.by_id['NOTE-002']
    assert support.source != engineering.source
    assert 'unverified' in support.description.lower()
    assert 'failed' in engineering.description.lower()
    assert tools.by_id['INC-001'].active
    assert tools.by_id['REL-001'].status == 'blocked'
    assert tools.by_id['REL-001'].related_record_ids == ['OPS-004']
