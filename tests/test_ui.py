from streamlit.testing.v1 import AppTest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_dashboard_loads_and_shows_synthetic_facts(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', '')
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == 'Praxis'
    assert any('84,000' in metric.value for metric in app.metric)
    assert app.button(key='run').disabled


def test_jev_selection_explains_disabled_state():
    app = AppTest.from_file(APP).run(timeout=30)
    app.sidebar.selectbox(key='decision_provider').select('jev').run()
    assert not app.exception
    assert app.button(key='run').disabled
    assert any('JEV' in warning.value for warning in app.warning)


def test_review_buttons_update_local_state_only(monkeypatch):
    from praxis.schemas import RunResult, Analysis
    from praxis.data import load_dataset
    from praxis.tools import BusinessTools
    from test_decisions_validation import example_briefing
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('OPENAI_API_KEY', '')
    app = AppTest.from_file(APP).run(timeout=30)
    app.session_state['result'] = RunResult(run_id='ui-test-only', question='Mocked UI test',
        briefing=example_briefing(), analysis=Analysis(findings=[dict(record_id='INC-001',
            source_ids=['INC-001'], observation='Integration unavailable.')]),
        metrics=BusinessTools(load_dataset()).calculate_business_metrics(), decisions=[], events=[],
        model='scripted-test-double', elapsed_seconds=0)
    app.session_state['approvals'] = {}
    app.run()
    assert not app.exception
    app.button(key='ui-test-only:0:approved').click().run()
    assert app.session_state['approvals']['ui-test-only:0'] == 'approved'
    app.button(key='ui-test-only:0:rejected').click().run()
    assert app.session_state['approvals']['ui-test-only:0'] == 'rejected'
    assert not app.exception
