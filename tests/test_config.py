from praxis.config import settings


def test_default_ignores_unselected_gateway(monkeypatch):
    monkeypatch.setattr('praxis.config.load_dotenv', lambda: None)
    monkeypatch.delenv('LLM_PROVIDER', raising=False)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('ANTHROPIC_AUTH_TOKEN', 'unselected-runtime-token')
    monkeypatch.setenv('ANTHROPIC_BASE_URL', 'http://localhost:20128')
    monkeypatch.setenv('ANTHROPIC_MODEL', 'unselected-alias')
    config = settings()
    assert config.provider == 'openai'
    assert not config.ready
    assert config.base_url is None
    assert 'unselected-runtime-token' not in repr(config)


def test_groq_uses_its_own_key_endpoint_and_full_model_id(monkeypatch):
    monkeypatch.setattr('praxis.config.load_dotenv', lambda: None)
    monkeypatch.setenv('LLM_PROVIDER', 'groq')
    monkeypatch.setenv('GROQ_API_KEY', 'groq-test-only')
    monkeypatch.delenv('GROQ_MODEL', raising=False)
    monkeypatch.delenv('GROQ_BASE_URL', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'wrong-provider-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://wrong-provider.invalid/v1')
    config = settings()
    assert config.provider == 'groq'
    assert config.model == 'openai/gpt-oss-120b'
    assert config.base_url == 'https://api.groq.com/openai/v1'
    assert config.api_key == 'groq-test-only'
    assert config.ready
    assert 'groq-test-only' not in repr(config)


def test_groq_does_not_borrow_another_provider_key(monkeypatch):
    monkeypatch.setattr('praxis.config.load_dotenv', lambda: None)
    monkeypatch.setenv('LLM_PROVIDER', 'groq')
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'wrong-provider-key')
    assert not settings().ready


def test_groq_model_override(monkeypatch):
    monkeypatch.setattr('praxis.config.load_dotenv', lambda: None)
    monkeypatch.setenv('LLM_PROVIDER', 'groq')
    monkeypatch.setenv('GROQ_MODEL', 'openai/gpt-oss-20b')
    assert settings().model == 'openai/gpt-oss-20b'
