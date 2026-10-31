# Praxis review — 2026-10-29

## Resolution in the React/JEV revision

The findings below are preserved as historical review evidence. The revision
adds per-record value/currency to the operating snapshot, displays monetary
cents, restricts prose references to declared/retrieved evidence, and strengthens
conditional-outcome/financial-missingness prompts. Regression tests cover these
changes. Historical saved model outputs were not rewritten as new results.

The new React/API source review also corrected pending-request state locking,
polling recovery, JEV cache-failure warnings, small-text contrast and offscreen
mobile navigation focus. A subsequent approved Chrome rehearsal produced ten
real captures and passed 21 checks. Independent visual review found no material
visible defect and returned ship for those captures, with mobile emulation and
accessibility scope limits retained.
See VERIFICATION.md for current tests, genuine runs and optional-provider limits.

## Original review

Scope: current application against the original Praxis specification. This
folder has no Git history, so there is no branch diff or commit baseline. Two
independent reviews covered correctness/documented standards and specification
coverage; findings below were then verified against code and saved live outputs.
Application code was not changed during this review.

Verdict: the app runs and its existing tests pass, but the financial grounding gap
should be fixed before recording. Three distinct code issues and one saved-output
quality issue were identified. One code issue appears in both review axes.

## Standards / correctness

1. **P1 — Individual financial evidence is omitted from the Groq workflow.**
   `src/praxis/schemas.py:119` defines `UpdateSummary` without `contract_value`
   or `currency`. `get_operating_snapshot()` projects records into that type,
   leaving only aggregate exposure and pipeline. At `src/praxis/agents/groq.py:13`,
   any tool result switches the model to final structured output and removes its
   tools, so the documented follow-up `get_record_details` is unavailable after
   a snapshot. The analyst cannot compare the USD 120,000 Summit proposal with
   the USD 32,000 and USD 20,000 opportunities. Their descriptions contain no
   amounts. Include authoritative financial fields in the compact projection,
   or allow detail retrieval before finalization. No arithmetic should move to
   the model. A review probe confirmed `SALE-001` has no amount in the snapshot.

2. **P2 — Exposure cards silently round supported monetary values.**
   `app.py:92` formats exposure with `:,.0f`, while the schema accepts cents.
   An AppTest using `CON-001.contract_value = Decimal('48000.25')` computed
   USD 84,000.25 but rendered **USD 84,000**, without a rounding label. Display
   two decimals, or identify the rounded figure and expose the exact total.

Standards/correctness: two findings; the financial grounding omission is the
highest severity. No additional high-confidence approval or credential-handling
defect was found within the documented single-user/local-only scope.

## Specification

1. **P1 — Per-record financial facts cannot inform default prioritization.**
   This is the same omission described above. The spec requires retrieving
   financial evidence and identifying a high-value proposal; aggregate pipeline
   cannot establish an individual proposal's value. The accepted morning result
   says “Financial contract values for cancellation cases are missing” at
   `artifacts/live-morning.json:76`, despite Willow's USD 36,000 contract being
   present in `CON-002`. Preserve those facts in the actual analyst input.

2. **P2 — Prose source references bypass the checked evidence scope.**
   `src/praxis/validation/__init__.py:50` checks summary/limitation IDs against
   the entire dataset, while line 66 does the same for priority prose. Structured
   citations are restricted to analyzed/directly related sources. A review probe
   let the analyst retrieve only Cedar details, then supplied a summary naming
   `SALE-001`; `validate_briefing` accepted it even though the analyst never
   retrieved that opportunity. Check summary IDs against analyzed sources and
   each priority/draft's embedded IDs against its declared supporting sources.
   Apply the same policy to analyst prose and limitations.

3. **P2 — The saved demonstration explanation overstates its evidence.**
   `artifacts/live-explanation.json:5` says the outage blocks the customer from
   signing the renewal, and line 31 asserts a revenue-recognition dependency.
   The records establish an unresolved incident and a requested recovery plan
   before renewal; they do not prove those outcomes or accounting treatment.
   This is a concrete recording-content issue, despite the documented limit
   that source validation is not semantic entailment verification. Use conditional
   language for inferred outcomes, and review the explanation against the actual
   deadline and customer statements before presenting it. Do not claim an
   automated general-purpose semantic verifier is already implemented.

Specification: three findings; the financial grounding omission is the highest
severity. Disabled JEV is permitted by the specification and is not a defect.

## Review evidence

- The running server's `/_stcore/health` returned **HTTP 200 / ok**.
- Existing offline suite: **48 passed, 2 live tests deselected, 82 warnings in
  16.72 seconds**, using `.venv/Scripts/python.exe -m pytest -m "not live" -q
  --disable-warnings --junitxml=artifacts/review-existing-tests.xml`.
- Review-only probes: **3 failed in 3.24 seconds**, reproducing the snapshot
  amount omission, unobserved prose citation and lost cents. Command:
  `.venv/Scripts/python.exe -m pytest .tmp/test_review_probes.py -q
  --disable-warnings --tb=short --junitxml=artifacts/review-probes.xml`.
  These failures document expected behavior missing from the current code;
  the probes are ignored temporary review files, not part of the normal suite.
- The saved real Groq outputs were inspected; no additional provider calls were
  made for this review. No credentials were read or printed.
- Native Chrome capture was attempted in an isolated headless profile, but Chrome's
  GPU subprocesses failed with access-denied crashes in this environment. No
  screenshot, keyboard-navigation or mobile visual review is claimed. The UI
  reproduction above used Streamlit AppTest, not a browser screenshot.

## Interface observations

The interface uses labeled native controls, separates deterministic KPIs from
model judgments, exposes supporting record descriptions, and states clearly
that approval is local. Existing tests cover disabled-provider states and local
review controls. Those are useful foundations to retain. The review does not
assign a visual accessibility/responsiveness score without browser evidence.

## Suggested order

1. Restore per-record financial evidence in the compact snapshot.
2. Enforce matching source scope for structured references and prose identifiers.
3. Preserve cents on exposure cards.
4. Run the regression probes, then regenerate and inspect both live scenarios.
5. Do one desktop browser rehearsal before recording the Loom.
