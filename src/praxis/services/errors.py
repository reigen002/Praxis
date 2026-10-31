"""Safe application errors that contain no provider response bodies."""
from math import ceil


class ProviderCooldown(RuntimeError):
    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = ceil(retry_after_seconds)
        # Avoid a throttling error name/message: CrewAI retries those automatically.
        super().__init__(f'Provider cooldown requires {self.retry_after_seconds} seconds')
