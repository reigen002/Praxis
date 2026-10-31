import pytest

from praxis.data import load_dataset
from praxis.schemas import Analysis, Briefing
from praxis.tools import BusinessTools
from praxis.validation import OutputRejected, validate_analysis, validate_briefing


def sourced_briefing():
    return Briefing.model_validate(dict(
        executive_summary='Customer recovery needs attention.',
        priorities=[dict(rank=1, record_id='INC-001', title='Verify recovery',
            category='support', urgency='Critical', business_impact='Renewal may be at risk.',
            recommended_action='Confirm recovery with engineering.', suggested_owner='Engineering',
            source_ids=['INC-001', 'CON-001'])],
        follow_ups=[dict(record_id='INC-001', recipient_team='Customer Success',
            draft='Please confirm recovery.', source_ids=['INC-001'])]))


def retrieved_analysis(tools, *, include_feature=False):
    tools.actor = 'Business Operations Analyst'
    tools.get_business_updates()
    findings = [dict(record_id='INC-001', source_ids=['INC-001', 'CON-001'],
        observation='The service incident may affect renewal.')]
    if include_feature:
        findings.append(dict(record_id='FEAT-001', source_ids=['FEAT-001'],
            observation='The feature request has no committed deadline.'))
    return validate_analysis(Analysis(findings=findings), tools)


@pytest.mark.parametrize('field', ['observation', 'assumptions'])
@pytest.mark.parametrize('reference', ['SALE-002', 'NOTE-001'])
def test_analyst_prose_cannot_reference_undeclared_evidence(field, reference):
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_record_details('INC-001')
    finding = dict(record_id='INC-001', source_ids=['INC-001'], observation='Recovery is unverified.')
    finding[field] = [f'Check {reference}.'] if field == 'assumptions' else f'Check {reference}.'
    with pytest.raises(OutputRejected, match='identifier'):
        validate_analysis(Analysis(findings=[finding]), tools)


def test_analyst_limitations_cannot_reference_unretrieved_records():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_record_details('INC-001')
    analysis = Analysis(findings=[dict(record_id='INC-001', source_ids=['INC-001'],
        observation='Recovery is unverified.')], limitations=['SALE-002 needs verification.'])
    with pytest.raises(OutputRejected, match='identifier'):
        validate_analysis(analysis, tools)


def test_analyst_limitations_can_reference_retrieved_records_outside_findings():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_record_details('INC-001')
    analysis = Analysis(findings=[dict(record_id='INC-001', source_ids=['INC-001'],
        observation='Recovery is unverified.')], limitations=['NOTE-001 is an unverified restoration report.'])
    assert validate_analysis(analysis, tools) == analysis


def test_chief_can_preserve_an_explicitly_validated_analyst_limitation():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_business_updates()
    analysis = validate_analysis(Analysis(findings=[dict(record_id='INC-001',
        source_ids=['INC-001', 'CON-001'], observation='Recovery remains unconfirmed.')],
        limitations=['CAN-002 lacks recorded contract evidence.']), tools)
    briefing = sourced_briefing()
    briefing.data_limitations = ['CAN-002 lacks recorded contract evidence.']
    assert validate_briefing(briefing, tools, analysis) == briefing


def test_analyst_can_compare_explicitly_cited_unlinked_retrieved_records():
    tools = BusinessTools(load_dataset())
    tools.actor = 'Business Operations Analyst'
    tools.get_business_updates(category='feature')
    analysis = Analysis(findings=[dict(record_id='FEAT-001', source_ids=['FEAT-001', 'FEAT-002'],
        observation='FEAT-001 and FEAT-002 have no committed delivery dates.')])
    assert validate_analysis(analysis, tools) == analysis


@pytest.mark.parametrize('field', ['title', 'business_impact', 'recommended_action', 'assumptions'])
def test_priority_prose_cannot_borrow_other_analyzed_evidence(field):
    tools = BusinessTools(load_dataset())
    analysis = retrieved_analysis(tools, include_feature=True)
    briefing = sourced_briefing()
    value = 'Compare FEAT-001 before proceeding.'
    setattr(briefing.priorities[0], field, [value] if field == 'assumptions' else value)
    with pytest.raises(OutputRejected, match='identifier'):
        validate_briefing(briefing, tools, analysis)


def test_follow_up_prose_must_cite_its_own_references():
    briefing = sourced_briefing()
    briefing.follow_ups[0].draft = 'Please confirm the decision for CON-001.'
    with pytest.raises(OutputRejected, match='identifier'):
        validate_briefing(briefing, BusinessTools(load_dataset()))


@pytest.mark.parametrize('field', ['executive_summary', 'data_limitations'])
@pytest.mark.parametrize('with_analysis', [False, True])
def test_briefing_prose_cannot_reference_records_outside_its_evidence(field, with_analysis):
    tools = BusinessTools(load_dataset())
    analysis = retrieved_analysis(tools) if with_analysis else None
    briefing = sourced_briefing()
    value = 'SALE-002 needs additional attention.'
    setattr(briefing, field, [value] if field == 'data_limitations' else value)
    with pytest.raises(OutputRejected, match='identifier'):
        validate_briefing(briefing, tools, analysis)


def test_briefing_summary_can_compare_analyzed_records_outside_priorities():
    tools = BusinessTools(load_dataset())
    analysis = retrieved_analysis(tools, include_feature=True)
    briefing = sourced_briefing()
    briefing.executive_summary = 'INC-001 takes precedence over FEAT-001 because renewal may be at risk.'
    assert validate_briefing(briefing, tools, analysis) == briefing
