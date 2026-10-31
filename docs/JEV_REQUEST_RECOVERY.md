# JEV duplicate-request diagnosis — 2026-10-31

The reported request `dec_d5ee569494f25ab372dd05b3` was checked with an
authenticated **GET**, not a new decision POST. The live response returned:

- HTTP 200; request status `success`; model `jev-1.13`.
- Completed at `2026-10-31T04:37:53.197Z`.
- `credits_used: 1`.
- Usage metadata: 1,574 prompt tokens and 95 completion tokens.
- No `answers` field. No accepted decision could be recovered from this response.

This is a duplicate-request response, not evidence of invalid credentials or a
malformed model answer. JEV returns HTTP409 when a request reuses an idempotency
key; it does not replay the original answer. The documented remedy is to inspect
the original request's status.
[Official decisions contract](https://jev-ai.org/docs/decisions/)

The old adapter retried transient failures with the same key but used only a
10-second answer timeout. If the first response was lost, a retry could receive
409 after the original succeeded. The exact initial transport/provider failure
was not retained, so timeout is a plausible cause rather than a confirmed log
event. The old adapter also saved only accepted successes: another browser click
or server restart generated a fresh key and could spend another credit.

## Correction

- Allow 30 seconds for an answer, with a separate 5-second connection timeout.
- Atomically persist each idempotency key before sending the decision request.
- Preserve unresolved requests in the existing ignored cache under `requests`,
  keyed by the same evidence/model/question fingerprint as successful decisions.
- After a conflict, persist the original request ID and read its status through
  a fixed HTTPS JEV URL. Never follow supplied URLs or redirects with credentials.
- Later clicks on that fingerprint only check the known original request. If a
  request ID was never received, reuse its saved key instead of generating one.
- Do not treat status metadata as a validated model decision. Surface a clear
  message and keep Rules available explicitly.
- Clear pending tracking after an accepted cached success or a documented
  uncharged HTTP failure. Preserve it for ambiguous transport failures and
  invalid HTTP200 answers.

The safeguard applies to requests tracked by the updated adapter. Older failed
requests did not retain their input fingerprint, so they cannot be automatically
associated with a record or retroactively recovered. Do not repeatedly evaluate
the earlier failed example to try to recover its answer.

## Demo recovery and limits

Use **Rules** for the YFS briefing. To show an existing genuine JEV result without
another model call, select **Startup demo**, record **INC-001**, then **View saved
live decision**. That saved answer must not be presented as a school decision.

The lost answer is not cached, simulated, or reconstructed from the rules result.
A genuinely new JEV evaluation may consume another credit. Only deliberately
authorize one after reviewing the provider's request status and remaining quota.
If an operator must clear a tracked request, stop the single-worker server, back
up `artifacts/jev-decisions.json`, and remove only that fingerprint's `requests`
entry. Never delete the entire cache or the genuine `decisions` entries.

The lock protects this single-process local demo. Multiple server processes are
not supported for shared-cache spending coordination. A longer timeout reduces
one failure cause but cannot guarantee delivery or recover an already lost answer.

## Verification scope

Mocked HTTP regression tests cover timeout → conflict → restart, status-only
rechecks, original-ID selection, credential/redirect safety, invalid answers,
cache-write failures, corrupt tracking, and explicit uncharged failures.
No new live JEV decision was submitted during this fix. The live verification
was limited to GET status checks; no new Cursor or Groq model call was made.
