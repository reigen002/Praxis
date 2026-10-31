import pytest
from pydantic import ValidationError
from praxis.data import load_dataset
from praxis.tools import BusinessTools
from praxis.decisions import RulesProvider, get_provider
from praxis.schemas import Briefing, Analysis
from praxis.validation import validate_analysis, validate_briefing, OutputRejected
from praxis.services.approvals import review_draft


def example_briefing():
    return Briefing.model_validate(dict(executive_summary='Customer recovery needs founder attention.',
        priorities=[dict(rank=1,record_id='INC-001',title='Restore integration',category='support',
            urgency='Critical',business_impact='Renewal may be at risk.',recommended_action='Verify recovery with engineering.',
            suggested_owner='Engineering',source_ids=['INC-001','CON-001'])],
        follow_ups=[dict(record_id='INC-001',recipient_team='Customer Success',draft='Please confirm recovery and share an update.',source_ids=['INC-001'])]))


def test_rules_policy_and_completed():
    tools = BusinessTools(load_dataset())
    provider = RulesProvider(tools)
    assert provider.evaluate(tools.by_id['INC-001']).urgency == 'Critical'
    assert provider.evaluate(tools.by_id['FEAT-001']).urgency == 'Routine'
    assert provider.evaluate(tools.by_id['DONE-001']).urgency == 'Routine'
    assert provider.evaluate(tools.by_id['CAN-002']).uncertainty


def test_provider_selection_is_explicit(monkeypatch):
    monkeypatch.delenv('JEV_API_KEY', raising=False)
    monkeypatch.setattr('praxis.decisions.load_dotenv', lambda: None, raising=False)
    tools = BusinessTools(load_dataset())
    assert isinstance(get_provider('rules', tools), RulesProvider)
    with pytest.raises(ValueError):
        get_provider('unknown', tools)
    with pytest.raises(ValueError, match='JEV_API_KEY'):
        get_provider('jev', tools)


def test_invalid_sources_rejected():
    tools = BusinessTools(load_dataset())
    briefing = example_briefing()
    briefing.priorities[0].source_ids.append('FAKE-001')
    with pytest.raises(OutputRejected):
        validate_briefing(briefing, tools)


@pytest.mark.parametrize('claim', ['Exposure is 999999 dollars.', 'A million dollars will be lost.', 'Churn risk is 90%.'])
def test_unsupported_numeric_claims_rejected(claim):
    briefing = example_briefing()
    briefing.priorities[0].business_impact = claim
    with pytest.raises(OutputRejected):
        validate_briefing(briefing, BusinessTools(load_dataset()))


def test_policy_cannot_be_downgraded():
    briefing = example_briefing()
    briefing.priorities[0].urgency = 'Routine'
    with pytest.raises(OutputRejected):
        validate_briefing(briefing, BusinessTools(load_dataset()))


def test_analysis_requires_actual_retrieval():
    tools = BusinessTools(load_dataset())
    analysis = Analysis(findings=[dict(record_id='INC-001',source_ids=['INC-001'],observation='Integration unavailable.')])
    with pytest.raises(OutputRejected, match='retrieval'):
        validate_analysis(analysis, tools)
    tools.actor = 'Business Operations Analyst'
    tools.get_business_updates()
    validate_analysis(analysis, tools)


def test_unrelated_valid_id_is_rejected():
    briefing = example_briefing()
    briefing.priorities[0].source_ids.append('SALE-002')
    with pytest.raises(OutputRejected):
        validate_briefing(briefing, BusinessTools(load_dataset()))


def test_approval_is_local_and_rejects_unknown_drafts():
    briefing = example_briefing()
    state = {}
    review_draft(state, 'run-a', briefing, 0, 'approved')
    assert state == {'run-a:0': 'approved'}
    review_draft(state, 'run-a', briefing, 0, 'rejected')
    assert state['run-a:0'] == 'rejected'
    with pytest.raises(ValueError):
        review_draft(state, 'run-a', briefing, 8, 'approved')


def test_structured_output_forbids_approval_bypass():
    data = example_briefing().model_dump()
    data['follow_ups'][0]['approval_required'] = False
    with pytest.raises(ValidationError):
        Briefing.model_validate(data)


def test_analysis_can_compare_retrieved_records_without_graph_link():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_business_updates()
    analysis = Analysis(findings=[dict(record_id='FEAT-001', source_ids=['FEAT-001', 'FEAT-002'],
        observation='Both feature requests lack committed delivery dates.')])
    assert validate_analysis(analysis, tools) == analysis


def test_valid_record_ids_in_prose_are_identifiers_not_numeric_claims():
    briefing = example_briefing()
    briefing.executive_summary = 'INC-001 threatens the renewal linked in CON-001.'
    assert validate_briefing(briefing, BusinessTools(load_dataset())) == briefing


def test_unknown_record_id_in_prose_is_rejected():
    briefing = example_briefing()
    briefing.executive_summary = 'FAKE-001 is the most urgent item.'
    with pytest.raises(OutputRejected):
        validate_briefing(briefing, BusinessTools(load_dataset()))


def test_wrong_category_feedback_identifies_authoritative_source_label():
    briefing = example_briefing()
    briefing.priorities[0].category = 'cancellation'
    with pytest.raises(OutputRejected, match='INC-001.*support'):
        validate_briefing(briefing, BusinessTools(load_dataset()))


def test_policy_guardrail_calls_are_attributed_to_validation_layer():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Chief of Staff'
    validate_briefing(example_briefing(), tools)
    assert tools.events[-1].actor == 'Output validation'
    assert tools.events[-1].tool == 'get_policy_escalations'
    assert tools.actor == 'Chief of Staff'
