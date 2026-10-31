# JEV authentication diagnosis — 2026-10-30

**Resolved after replacing the key.** The corrected credential passed the models
authentication check with HTTP200. One real INC-001 decision returned Engineering,
Critical, expected score 2.97/3 and risk estimate 0.86. It used one credit and was
saved for reuse; the running comparison API now returns `cached=true`.

**Original cause: credential/provider mismatch.** The earlier `JEV_API_KEY` had
OpenRouter format, while this adapter calls `jev-ai.org`.

The read-only `GET https://jev-ai.org/api/v1/models/` check returned HTTP401,
reason `unknown_key`. The selected credential matches `.env`; there is no shell
override, whitespace, masked ellipsis or duplicate Groq key. No secret was printed.
The latest sanitized `artifacts/jev-auth-diagnostic.json` now records successful
authentication; the failed decision test remains as historical XML evidence.

No decision-model requests were made to diagnose the original cause. The models check
is documented as uncharged in [JEV authentication](https://jev-ai.org/docs/authentication/).

Use the full key created in [JEV Settings → API keys](https://jev-ai.org/settings/apikeys/)
for this adapter. OpenRouter credentials belong to
[OpenRouter's API](https://openrouter.ai/docs/api/reference/authentication), a
separate host/integration. Keep the current key private; it was not modified.

The adapter now rejects known OpenRouter keys before an HTTP decision request
and preserves safe documented authentication reasons. Unknown reason text is
never reflected into errors. Unit tests cover these behaviors without live calls.
