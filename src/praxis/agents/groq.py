"""Groq compatibility for CrewAI 1.15.33's zero-argument tool schemas."""
import json
from math import isfinite
from time import monotonic
from crewai.llms.providers.openai.completion import OpenAICompletion
from openai import RateLimitError
from pydantic import BaseModel
from praxis.services.errors import ProviderCooldown


class GroqCompletion(OpenAICompletion):
    final_response_model: type[BaseModel] | None = None
    request_deadline: float | None = None

    def _handle_completion(self, params, available_functions=None, from_task=None,
            from_agent=None, response_model=None):
        if response_model is None:
            return super()._handle_completion(params, available_functions, from_task,
                from_agent, response_model)
        # JSON object mode avoids Groq's observed constrained-decoder failures.
        # The same Pydantic model and task evidence guardrails remain authoritative.
        structured = dict(params, response_format={'type': 'json_object'},
            messages=[*params['messages'], {'role': 'user', 'content':
                'Return a concise JSON object matching this schema exactly. '
                'Include every required field and no extra fields. '
                + json.dumps(response_model.model_json_schema())}])
        raw = super()._handle_completion(structured, available_functions, from_task, from_agent)
        return response_model.model_validate_json(raw)

    def call(self, messages, tools=None, callbacks=None, available_functions=None, **kwargs):
        if self.request_deadline is not None:
            remaining = self.request_deadline - monotonic()
            if remaining <= 0:
                raise TimeoutError('The briefing provider time budget expired')
            self._client = self._get_sync_client().with_options(timeout=min(self.timeout or 35, remaining))
        # After a real tool result, finalize using Groq's structured-output mode.
        # Groq does not support a JSON schema and function tools in the same call.
        if self.final_response_model and tools and isinstance(messages, list) and any(
                message.get('role') == 'tool' for message in messages):
            tools = None
            available_functions = None
            kwargs['response_model'] = self.final_response_model
        cooldown = None
        try:
            return super().call(messages, tools=tools, callbacks=callbacks,
                available_functions=available_functions, **kwargs)
        except RateLimitError as error:
            # CrewAI 1.15.33 reads dict-valued error.headers, not httpx response headers.
            # Short waits use CrewAI's native retry. Long waits fail immediately;
            # its thread timeout cannot interrupt a provider retry sleeping here.
            error.headers = dict(error.response.headers)
            hint = error.headers.get('retry-after')
            if hint is not None:
                try:
                    delay = float(hint)
                    if not isfinite(delay) or delay < 0:
                        raise ValueError('Invalid retry delay')
                    wait = max(1.0, delay) + 1.0
                    remaining = (self.request_deadline - monotonic()
                        if self.request_deadline is not None else float('inf'))
                    if wait > min(60, remaining):
                        cooldown = ProviderCooldown(delay)
                    else:
                        error.headers['retry-after'] = str(wait)
                except ValueError:
                    error.headers.pop('retry-after', None)
            if cooldown is None:
                raise
        # Raise outside the except block so the original 429 is not an implicit
        # context: CrewAI traverses that chain and would retry it again.
        raise cooldown

    def _convert_tools_for_interference(self, tools):
        converted = super()._convert_tools_for_interference(tools)
        for tool in converted:
            parameters = tool['function'].get('parameters', {})
            if parameters.get('type') == 'object':
                parameters.setdefault('properties', {})
                # Groq treats empty properties as absent when required is present.
                if not parameters['properties']:
                    parameters.pop('required', None)
        return converted
