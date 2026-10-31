import pytest
import os

os.environ['CREWAI_TELEMETRY_DISABLED'] = 'true'
os.environ['OTEL_SDK_DISABLED'] = 'true'


def pytest_addoption(parser):
    parser.addoption('--live', action='store_true', help='Run paid/networked provider integration tests')


def pytest_collection_modifyitems(config, items):
    if not config.getoption('--live'):
        for item in items:
            if 'live' in item.keywords:
                item.add_marker(pytest.mark.skip(reason='Pass --live to opt in to real provider calls'))
