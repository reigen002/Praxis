"""Run with: uv run --frozen streamlit run app.py"""
from dataclasses import replace
from hashlib import sha256
import streamlit as st
from pydantic import ValidationError
from praxis.config import settings
from praxis.data import load_dataset
from praxis.decisions import RulesProvider
from praxis.schemas import Dataset
from praxis.services.approvals import review_draft
from praxis.services.briefing import BriefingFailed, run_briefing
from praxis.tools import BusinessTools

st.set_page_config(page_title='Praxis | Chief of Staff', page_icon='P', layout='wide')
MORNING = 'Prepare my founder briefing for today. What are the three most important issues, and why?'
EXPLAIN = 'Why is the customer renewal issue more urgent than the feature request?'


def evidence_table(records):
    return [dict(ID=r.record_id, Title=r.title, Status=r.status, Category=r.category,
        Deadline=str(r.deadline) if r.deadline else 'Not recorded',
        Amount=f'{r.currency} {r.contract_value:,.2f}' if r.contract_value is not None else 'Not recorded',
        Owner=r.owner or 'Unassigned') for r in records]


def show_events(events):
    st.caption('Recorded tool completions and task outcomes. No internal reasoning is displayed.')
    st.dataframe([dict(Time=e.timestamp.strftime('%H:%M:%S UTC'), Actor=e.actor, Event=e.kind,
        Tool=e.tool or '', Records=', '.join(e.source_ids), Result=e.detail) for e in events],
        hide_index=True, width='stretch')


try:
    config = settings()
except ValueError:
    st.error('Invalid provider configuration. Set LLM_PROVIDER to anthropic, openai or groq in .env.')
    st.stop()

with st.sidebar:
    st.title('Praxis')
    st.caption('AI CHIEF OF STAFF')
    st.divider()
    st.markdown('**SYNTHETIC DEMONSTRATION DATA**')
    dataset_choice = st.selectbox('Dataset', ['Startup operations · 28 updates', 'Upload synthetic JSON'])
    upload = st.file_uploader('Synthetic dataset', type=['json']) if dataset_choice.startswith('Upload') else None
    selected_provider = st.selectbox('Decision signals', ['rules', 'jev'],
        index=1 if config.decision_provider == 'jev' else 0, key='decision_provider')
    st.caption('Rules are deterministic. JEV is an optional, currently disabled integration.')
    st.divider()
    st.markdown('**Agent readiness**')
    st.write('Credentials detected' if config.ready else 'Credentials required')
    st.caption('Connectivity is verified only by a successful run.')
    st.text(f'{config.provider} / {config.model}')
    st.markdown('**Example questions**')
    if st.button('Morning briefing', width='stretch'):
        st.session_state['question'] = MORNING
    if st.button('Explain the renewal risk', width='stretch'):
        st.session_state['question'] = EXPLAIN
    st.divider()
    st.caption('Every follow-up requires review. Approvals stay in this browser session.')

try:
    if dataset_choice.startswith('Upload'):
        if upload is None:
            st.info('Select a synthetic JSON dataset to continue.')
            st.stop()
        if upload.size > 1_000_000:
            st.error('Use a JSON file smaller than one megabyte.')
            st.stop()
        dataset = Dataset.model_validate_json(upload.getvalue())
    else:
        dataset = load_dataset()
except (ValidationError, ValueError, OSError):
    st.error('Dataset rejected. Check the JSON structure, unique IDs, related records, dates and monetary fields.')
    st.stop()

business = BusinessTools(dataset)
metrics = business.calculate_business_metrics()
fingerprint = sha256(dataset.model_dump_json().encode()).hexdigest()
context_key = (fingerprint, selected_provider, config.provider, config.model)
if st.session_state.get('context_key') != context_key:
    for key in ('result', 'failed_events', 'approvals'):
        st.session_state.pop(key, None)
    st.session_state['context_key'] = context_key

st.title('Praxis')
st.markdown('### Your operating picture, with the evidence attached.')
st.caption(f'SYNTHETIC DEMONSTRATION DATA · Reference date {dataset.reference_date:%d %B %Y} · {len(dataset.records)} updates')
st.caption('“Today” means the dataset reference date. Deadlines do not drift with the recording date.')

columns = st.columns(4)
exposure = ' · '.join(f'{currency} {value:,.2f}' for currency, value in metrics.exposure_by_currency.items()) or 'None recorded'
columns[0].metric('Recorded contract exposure', exposure)
columns[1].metric('Open issues', metrics.open_issues)
columns[2].metric('Overdue internal tasks', metrics.overdue_tasks)
columns[3].metric('Customer escalations', metrics.customer_escalations)
st.caption('Facts calculated from records. Exposure is contract face value linked to unresolved customer issues; it is not predicted loss.')

question = st.text_area('What needs your attention?', value=MORNING, key='question', max_chars=2000, height=95)
if selected_provider == 'jev':
    st.warning('JEV is disabled in this demonstration build. Select rules to run. No automatic fallback occurs.')
if not config.ready:
    st.info('Add provider credentials to .env to run the two CrewAI agents. You can inspect the real dataset and deterministic facts below.')
if st.button('Run founder briefing', type='primary', key='run', disabled=not config.ready or selected_provider != 'rules'):
    st.session_state.pop('result', None)
    st.session_state.pop('failed_events', None)
    with st.status('Running the analyst and Chief of Staff…', expanded=True) as status:
        st.write('Retrieving evidence, validating findings, and preparing recommendations. This may take several minutes.')
        try:
            result = run_briefing(question, dataset, replace(config, decision_provider=selected_provider))
        except BriefingFailed as exc:
            status.update(label='Briefing was not accepted', state='error')
            st.error(str(exc))
            st.session_state['failed_events'] = exc.events
        else:
            st.session_state['result'] = result
            st.session_state['approvals'] = {}
            status.update(label='Briefing accepted · evidence checks passed', state='complete')

result = st.session_state.get('result')
if result:
    briefing = result.briefing
    st.divider()
    st.subheader('Executive summary')
    st.caption(f'Accepted live run · {result.model} · {result.elapsed_seconds:g}s · Rules decision signals')
    st.caption(f'Question answered: {result.question}')
    st.write(briefing.executive_summary)
    st.caption('AI interpretation: structure and source references checked. Meaning and recommendations still require your review.')
    priorities, followups, evidence, execution = st.tabs(['Top priorities', 'Follow-up review', 'Source records', 'Execution & decisions'])
    with priorities:
        for priority in briefing.priorities:
            with st.container(border=True):
                st.subheader(f'{priority.rank:02d}  {priority.title}')
                st.caption(f'{priority.urgency.upper()} · {priority.category} · Suggested owner: {priority.suggested_owner}')
                st.markdown('**Model judgment — business impact**')
                st.write(priority.business_impact)
                st.markdown('**Recommended action**')
                st.write(priority.recommended_action)
                if priority.assumptions:
                    st.write('Assumptions / missing information: ' + '; '.join(priority.assumptions))
                with st.expander('Facts & supporting records · ' + ', '.join(priority.source_ids)):
                    st.dataframe(evidence_table([business.by_id[i] for i in priority.source_ids]), hide_index=True, width='stretch')
                    for record_id in priority.source_ids:
                        st.markdown(f'**{record_id}**')
                        st.write(business.by_id[record_id].description)
        st.markdown('**Data limitations**')
        for limitation in briefing.data_limitations:
            st.write('• ' + limitation)
        st.caption('Source validity does not prove semantic entailment. Conflicting restoration notes require human confirmation.')
    with followups:
        st.info('Review only. Approve and reject change local session state; no message is sent.')
        for index, draft in enumerate(briefing.follow_ups):
            with st.container(border=True):
                st.markdown(f'**Draft for {draft.recipient_team}** · {draft.record_id}')
                st.write(draft.draft)
                left, right, state_column = st.columns([1, 1, 3])
                for column, decision in [(left, 'approved'), (right, 'rejected')]:
                    if column.button('Approve locally' if decision == 'approved' else 'Reject', key=f'{result.run_id}:{index}:{decision}'):
                        review_draft(st.session_state['approvals'], result.run_id, briefing, index, decision)
                state_column.write('Review state: ' + st.session_state['approvals'].get(f'{result.run_id}:{index}', 'pending'))
    with evidence:
        ids = sorted({i for p in briefing.priorities for i in p.source_ids})
        st.dataframe(evidence_table([business.by_id[i] for i in ids]), hide_index=True, width='stretch')
    with execution:
        show_events(result.events)
        st.markdown('**Decision signals — deterministic rules, not probabilities**')
        st.dataframe([d.model_dump(exclude={'probabilities','risk_probability'}) for d in result.decisions], hide_index=True, width='stretch')
        with st.expander('Validated analyst findings'):
            st.json(result.analysis.model_dump(mode='json'))
        st.download_button('Download accepted run', result.model_dump_json(indent=2), file_name='praxis-briefing.json', mime='application/json')
elif st.session_state.get('failed_events'):
    with st.expander('Execution events from failed attempt', expanded=True):
        show_events(st.session_state['failed_events'])
else:
    st.info('Run a briefing to see agent recommendations. The evidence below is available before an agent run.')

with st.expander('Dataset & metric definitions', expanded=not bool(result)):
    data_tab, metrics_tab, baseline_tab = st.tabs(['Business records', 'Metric definitions', 'Rules baseline'])
    with data_tab:
        st.dataframe(evidence_table(dataset.records), hide_index=True, width='stretch')
        selected_id = st.selectbox('Inspect source record', list(business.by_id))
        st.json(business.by_id[selected_id].model_dump(mode='json'))
    with metrics_tab:
        st.write('Active sales pipeline: ' + ' · '.join(f'{c} {v:,.2f}' for c,v in metrics.pipeline_by_currency.items()))
        st.write(f'Opportunities awaiting action: {metrics.opportunities_awaiting_action}')
        st.write('Missing financial evidence: ' + (', '.join(metrics.missing_financial_ids) or 'None'))
        for name, definition in metrics.definitions.items():
            st.markdown(f'**{name.replace("_", " ").title()}**')
            st.write(definition)
        st.json(metrics.cohorts)
    with baseline_tab:
        baseline = RulesProvider(business)
        st.caption('Computed now from source fields. This is not an agent briefing or live JEV output.')
        st.dataframe([baseline.evaluate(r).model_dump(include={'record_id','classification','urgency','urgency_score','provider'}) for r in dataset.records], hide_index=True, width='stretch')
