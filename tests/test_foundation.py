from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError
from praxis.data import load_dataset
from praxis.schemas import Dataset, Record
from praxis.tools import BusinessTools


def test_dataset_and_stable_ids():
    data = load_dataset()
    assert len(data.records) == 28
    assert data.reference_date == date(2026, 10, 29)
    assert data.label == 'SYNTHETIC DEMONSTRATION DATA'
    assert len({r.record_id for r in data.records}) == 28


def test_duplicates_rejected():
    data = load_dataset().model_dump()
    data['records'].append(data['records'][0])
    with pytest.raises(ValidationError, match='Duplicate'):
        Dataset.model_validate(data)


@pytest.mark.parametrize('change', [dict(deadline='tomorrow'), dict(contract_value='-1'),
    dict(created_at='not-a-date'), dict(currency='money'), dict(related_record_ids=['MISSING'])])
def test_invalid_data(change):
    data = load_dataset().model_dump()
    data['records'][0].update(change)
    with pytest.raises(ValidationError):
        Dataset.model_validate(data)


def test_money_is_decimal_and_missing_is_not_zero():
    tools = BusinessTools(load_dataset())
    assert tools.by_id['CON-001'].contract_value == Decimal('48000.00')
    assert tools.by_id['CAN-002'].contract_value is None
    metrics = tools.calculate_business_metrics()
    assert metrics.exposure_by_currency == {'USD': Decimal('84000.00')}
    assert metrics.pipeline_by_currency == {'USD': Decimal('172000.00')}
    assert 'CAN-002' in metrics.missing_financial_ids


def test_metrics_and_completed_exclusion():
    tools = BusinessTools(load_dataset())
    metrics = tools.calculate_business_metrics()
    assert metrics.open_issues == 11
    assert metrics.overdue_tasks == 3
    assert metrics.customer_escalations == 4
    assert metrics.opportunities_awaiting_action == 3
    assert 'DONE-001' not in metrics.source_ids


def test_deadline_boundaries():
    tools = BusinessTools(load_dataset())
    risks = {r.record_id: r for r in tools.get_deadline_risks(7).risks}
    assert risks['OPS-002'].days_remaining == 0
    assert not risks['OPS-002'].overdue
    assert risks['OPS-003'].days_remaining == 7
    assert risks['OPS-001'].overdue
    assert 'FEAT-001' not in risks
    assert 'DONE-001' not in risks


def test_policy_requires_unresolved_critical_incident_and_related_contract():
    tools = BusinessTools(load_dataset())
    result = tools.get_policy_escalations()
    assert [e.record_id for e in result.escalations] == ['INC-001']
    assert set(result.escalations[0].source_ids) == {'INC-001', 'CON-001'}
    data = load_dataset().model_dump()
    data['records'][0]['status'] = 'completed'
    assert BusinessTools(Dataset.model_validate(data)).get_policy_escalations().escalations == []


def test_filters_details_and_trace():
    tools = BusinessTools(load_dataset())
    result = tools.get_business_updates(category='sales', status='open')
    assert len(result.records) == 3
    details = tools.get_record_details('INC-001')
    assert 'CON-001' in details.source_ids
    assert tools.events[-1].tool == 'get_record_details'
    with pytest.raises(ValueError, match='Unknown'):
        tools.get_record_details('NOPE')


def test_conflicting_contract_amounts_rejected():
    data = load_dataset().model_dump()
    row = data['records'][1].copy()
    row.update(record_id='CON-999', contract_value='99999')
    data['records'].append(row)
    with pytest.raises(ValidationError, match='contract'):
        Dataset.model_validate(data)


def test_operating_snapshot_keeps_evidence_and_computed_facts():
    tools = BusinessTools(load_dataset())
    snapshot = tools.get_operating_snapshot()
    assert len(snapshot.updates) == 28
    assert snapshot.updates[0].description == tools.by_id['INC-001'].description
    assert snapshot.metrics.exposure_by_currency == {'USD': Decimal('84000.00')}
    assert snapshot.policy.escalations[0].record_id == 'INC-001'
    assert set(snapshot.source_ids) == set(tools.by_id)
    assert [e.tool for e in tools.events] == ['get_business_updates', 'calculate_business_metrics',
        'get_deadline_risks', 'get_policy_escalations', 'get_operating_snapshot']
