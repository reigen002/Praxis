"""Real CrewAI execution with a scripted test double, never a live model claim."""
import json
from typing import Any
from crewai import BaseLLM
from praxis.agents import build_crew
from praxis.config import Settings
from praxis.data import load_dataset
from praxis.tools import BusinessTools
from test_decisions_validation import example_briefing


class ScriptedLLM(BaseLLM):
    step: int = 0
    chief_received_findings: bool = False

    def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs) -> str:
        text = json.dumps(messages)
        if 'Chief of Staff' in text:
            self.chief_received_findings = 'Integration remains unavailable.' in text
            return 'Final Answer: ' + example_briefing().model_dump_json()
        self.step += 1
        if self.step == 1:
            return 'Action: get_business_updates\nAction Input: {}'
        return 'Final Answer: ' + json.dumps(dict(findings=[dict(record_id='INC-001',
            source_ids=['INC-001', 'CON-001'], observation='Integration remains unavailable.')], limitations=[]))

    def supports_function_calling(self):
        return False

    def get_context_window_size(self):
        return 32000


def test_sequential_crew_passes_validated_context_and_records_real_tool_event(monkeypatch):
    scripted = ScriptedLLM(model='scripted-test-double')
    monkeypatch.setattr('praxis.agents.LLM', lambda **kwargs: scripted)
    business = BusinessTools(load_dataset())
    crew = build_crew(business, Settings('openai', 'test-only', 'test-key'), [], 'Brief me')
    output = crew.kickoff()
    assert scripted.chief_received_findings
    assert output.pydantic.priorities[0].record_id == 'INC-001'
    assert any(e.tool == 'get_business_updates' and e.actor == 'Business Operations Analyst' for e in business.events)
    assert [e.actor for e in business.events if e.kind == 'task'] == ['Business Operations Analyst', 'Chief of Staff']
