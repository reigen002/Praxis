# Cursor key compatibility

Checked against official documentation on 2026-10-31. No authenticated Cursor
requests, paid model calls, credential inspection, or application changes were made.

**A Cursor-issued API key cannot directly replace the Groq key in this app.**
Cursor explicitly documents its Cloud Agents API and SDKs as agent workflows,
not standalone model inference or chat completions. Changing only the key or
base URL would not provide the protocol this CrewAI application expects.
[Cursor API overview](https://cursor.com/docs/api)

## Which key matters

| Credential | Can it replace this app's Groq credential? |
| --- | --- |
| Cursor user API key | Not directly. It authenticates supported Cursor agent services. |
| Cursor team Admin API key | Not a model provider key; the Python agent SDK also excludes this key type. |
| OpenAI or Anthropic key entered in Cursor Settings → Models | Potentially, using the app's corresponding provider configuration and the provider's billing. It remains a third-party provider key. |

Cursor's Python SDK accepts user and service account API keys, and its usage
follows Cursor agent pricing and request pools. A Cursor key is therefore not
evidence of free inference capacity.
[Python SDK authentication and billing](https://cursor.com/docs/sdk/python)

Cursor's bring-your-own-key setting lets Cursor use an independently issued
provider key; that provider bills model usage. This does not turn a Cursor-issued
key into an OpenAI or Anthropic API key.
[Bring your own API key](https://cursor.com/help/models-and-usage/api-keys)

## Could a custom integration work?

The current Python SDK supports a local agent, text results, and `tools=[]` to
disable built-in tools. It also exposes custom Python tools. These are useful
integration primitives, so using Cursor programmatically is possible. They still
run Cursor's agent runtime and do not expose an interchangeable chat-completions
transport.
[Python SDK tools and runtime](https://cursor.com/docs/sdk/python)

Cursor's headless CLI supports noninteractive prompts and JSON output. Wrapping
that process would similarly run a Cursor agent rather than replace an inference
endpoint. Its JSON output option does not itself establish compatibility with
this app's Pydantic output contracts or CrewAI tool protocol.
[Headless CLI](https://cursor.com/docs/cli/headless)

**Engineering assessment:** a custom integration would need deliberate handling
of tool ownership, structured-output validation, permissions, lifecycle, errors,
and cancellation. It would need new end-to-end verification to preserve the
project's two-agent CrewAI requirement. No Cursor latency benchmark was run, so
there is no basis to claim it would be faster than the existing setup.

## Existing application boundary

Inspection of `src/praxis/config.py` shows supported providers are Groq,
OpenAI, and Anthropic. `src/praxis/agents/__init__.py` builds the CrewAI LLM
with a provider-specific key and base URL. `src/praxis/agents/groq.py` adapts
the OpenAI-compatible Groq transport, tool schemas, and Pydantic conversion.

For this demo, keep a supported inference provider. Diagnose end-to-end time
separately from provider generation speed: tool rounds, structured-output
correction, and rate-limit waits can all contribute. Changing credentials alone
does not remove those stages. Any replacement must be measured on the same
briefing and evidence-validation checks before calling it an improvement.
