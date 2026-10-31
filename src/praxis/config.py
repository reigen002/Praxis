import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    api_key: str = field(repr=False)
    base_url: str | None = None
    decision_provider: str = 'rules'
    jev_record_id: str | None = None

    @property
    def ready(self):
        return bool(self.api_key)


def settings() -> Settings:
    load_dotenv()
    os.environ['CREWAI_TELEMETRY_DISABLED'] = 'true'
    os.environ['OTEL_SDK_DISABLED'] = 'true'
    provider = os.getenv('LLM_PROVIDER', 'openai').lower()
    if provider not in ('anthropic', 'openai', 'groq'):
        raise ValueError('LLM_PROVIDER must be anthropic, openai or groq')
    prefix = provider.upper()
    key = os.getenv(prefix + '_API_KEY') or (os.getenv('ANTHROPIC_AUTH_TOKEN', '') if provider == 'anthropic' else '')
    default_model = {'anthropic': 'claude-sonnet-4-5-20250929',
        'openai': 'gpt-4.1-mini', 'groq': 'openai/gpt-oss-120b'}[provider]
    default_url = 'https://api.groq.com/openai/v1' if provider == 'groq' else None
    return Settings(provider, os.getenv(prefix + '_MODEL', default_model), key,
        os.getenv(prefix + '_BASE_URL') or default_url, os.getenv('DECISION_PROVIDER', 'rules'),
        os.getenv('JEV_RECORD_ID') or None)
