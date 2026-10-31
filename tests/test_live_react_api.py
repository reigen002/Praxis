"""Opt-in real provider checks, separate from offline/mocked integration tests."""
import json
from decimal import Decimal
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from praxis.api import app


@pytest.mark.live
@pytest.mark.parametrize('scenario,dataset,question', [
    ('morning', 'demo', 'Prepare my founder briefing for today. What are the three most important issues, and why?'),
    ('explanation', 'demo', 'Why is the customer renewal issue more urgent than the feature request?'),
    ('yfs-morning', 'yfs', 'Prepare my founder briefing for today. What are the three most important issues, and why?'),
    ('yfs-explanation', 'yfs', 'Why is the cohort access issue more urgent than the certificate preview redesign?')])
def test_live_enhanced_dataset_briefing_through_react_api(scenario, dataset, question):
    client = TestClient(app)
    started = client.post('/api/runs', json={'dataset': dataset, 'decision_provider': 'rules',
        'question': question})
    assert started.status_code == 202, started.text
    deadline = time.monotonic() + 400
    while time.monotonic() < deadline:
        body = client.get('/api/runs/' + started.json()['id']).json()
        if body['status'] in ('completed', 'failed'):
            break
        time.sleep(1)
    path = Path(f'artifacts/react-api-{scenario}.json')
    path.write_text(json.dumps(body, indent=2), encoding='utf-8')
    assert body['status'] == 'completed', body.get('error')
    result = body['result']
    assert result['mode'] == 'live'
    assert result['briefing']['priorities'][0]['record_id'] == 'INC-001'
    currency, exposure = ('INR', '300000') if dataset == 'yfs' else ('USD', '84000')
    assert Decimal(result['metrics']['exposure_by_currency'][currency]) == Decimal(exposure)
    assert result['briefing']['follow_ups']
    if scenario.endswith('morning'):
        assert len(result['briefing']['priorities']) == 3
    assert any(event['actor'] == 'Business Operations Analyst' and event['tool'] == 'get_business_updates'
        for event in result['events'])
    assert len([event for event in result['events'] if event['kind'] == 'task']) == 2
    if scenario.endswith('explanation'):
        assert any(finding['record_id'] == 'FEAT-001' for finding in result['analysis']['findings'])
