import json
import platform
from pathlib import Path
from importlib.metadata import version
from praxis.data import load_dataset
from praxis.decisions import RulesProvider
from praxis.tools import BusinessTools


def test_environment_versions_and_locked_dependencies():
    import crewai
    assert hasattr(crewai, 'Crew')
    assert platform.python_version_tuple()[:2] == ('3', '12')
    assert Path('uv.lock').exists()
    report = dict(python=platform.python_version(), dependencies={name: version(name)
        for name in ['crewai', 'streamlit', 'pydantic', 'pytest', 'httpx', 'python-dotenv', 'fastapi', 'uvicorn']})
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/environment.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def test_labeled_rules_fixture():
    fixture = json.loads(Path('data/synthetic/evaluation.json').read_text())
    tools = BusinessTools(load_dataset())
    provider = RulesProvider(tools)
    results = [(label, provider.evaluate(tools.by_id[label['record_id']])) for label in fixture]
    assert len(results) == 10
    for label, decision in results:
        assert decision.classification == label['classification']
        assert decision.urgency == label['urgency']
