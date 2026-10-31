# Verification and handover — Praxis workspace, 2026-10-31

## Praxis rename verification

The application, Python distribution/import package, React brand, browser title,
Streamlit titles, CLI, startup scripts, exports, package metadata and active
documentation now use Praxis (`praxis` for Python imports). Launch with
`uv run --frozen --cache-dir .cache/uv python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8000`.
The installed distribution was rebuilt using `uv lock --offline` and
`uv sync --frozen --offline`, both with the project cache directory.

One synthetic record had a wording-only application-name change. Three matching
saved-briefing fingerprints were migrated and revalidated; original model outputs,
run IDs, decisions, event timestamps, durations and saved timestamps were retained.
Credentials and the JEV response/request cache were not modified. The API returns
`application=Praxis`, all three school snapshots without warnings, and the same
genuine cached startup JEV request `dec_14499424bdea53337df1163b`.

Validation: **175 offline Python tests passed, 6 live deselected**, 38.60 seconds;
**10 React tests passed**; TypeScript and production build passed. The separate
Chrome saved-demo rehearsal passed **28 checks** with **13 screenshots**, zero
POSTs and no new inference. It checked Praxis branding, desktop/mobile layout,
saved briefings, evidence, local approvals, original execution activity, the
`praxis-briefing.json` export and cached JEV. Desktop and mobile captures were
visually inspected. The active project source and compiled frontend have no
remaining previous-name references. Historical generated artifacts and local
rollback backups are retained as evidence, not rewritten as new executions.

Evidence: `artifacts/praxis-rename.json`, `artifacts/praxis-rename-tests.xml`,
and `artifacts/rehearsal-praxis-saved/report.json`. No new live Groq or JEV call
was made for this rename; fresh inference still depends on provider availability.

## Demo readiness: repeatable saved executions

**READY WITH LIMITATIONS:** the complete prepared walkthrough works in the actual
browser; fresh inference remains dependent on provider quota/latency. This pass
made no new Groq or JEV model calls and does not claim fresh live inference was
reverified. The saved runs are genuine prior accepted executions, revalidated
against the current school dataset, and explicitly labeled historical in the UI.

- Python: **175 passed, 6 live deselected**, 36.69 seconds. Evidence:
  `artifacts/demo-ready-offline-tests.xml`.
- React: **10 passed**. TypeScript and production Vite build passed.
- Separate Chrome rehearsal: **27 passing checks**, **13 screenshots**, zero
  POSTs, one read-only cached JEV GET, zero uncaught browser exceptions. Evidence:
  `artifacts/rehearsal-saved/report.json`. Saved choices, briefing and JEV captures
  were visually inspected. Desktop 1440×1000 and 1366×768, mobile 390×844 had no
  page overflow in the checked states.
- Checked saved morning and explanation, deterministic metrics, evidence links,
  missing feature deadline, local approve/reject, original agent activity, JSON
  export, saved-run availability after refresh, and genuine cached JEV display.
- New runs persist automatically after acceptance. Corrupt or changed-evidence
  snapshots are withheld. Storage failure keeps an accepted live answer usable
  and directs the user to export it. No UI upload/import of arbitrary runs exists.
- Backend and compiled React app respond at `http://127.0.0.1:8000`; the school
  endpoint contains two accepted saved briefings with no validation warnings.

Changed: `services/saved_runs.py`, `api.py`, `SavedBriefings.tsx`, `App.tsx`,
`types.ts`, `styles.css`, Python/React tests, `scripts/prepare-demo.py`,
`scripts/rehearse-desktop.mjs`, README and demo documentation. No dependency or
credential changes. See [TEST_DRIVE.md](TEST_DRIVE.md) for the user sequence.

## Latest correction: interrupted JEV requests

`tests/test_jev.py`: **71 passed** using mocked HTTP. Full offline suite:
**165 passed, 6 live tests deselected**, 146 upstream warnings, 32.23 seconds.
Evidence: `artifacts/jev-retry-offline-tests.xml`.

```powershell
.venv/Scripts/python.exe -m pytest -m 'not live' -q --tb=short --junitxml=artifacts/jev-retry-offline-tests.xml
```

The request reported by the user was read through the authenticated JEV status
endpoint. It reports success and one credit used, but has no answer payload.
No new JEV decision, Groq inference, or Cursor inference was requested during
this correction. See [the diagnosis and recovery limits](JEV_REQUEST_RECOVERY.md).

The adapter now saves request identity before sending, retains ambiguous requests
across restarts, checks known original requests through a fixed-origin GET, and
uses a 30-second read timeout. Mocked regressions reproduce the lost-response
conflict, check status without spending again, and preserve genuine cached results.
This does not recover older lost answers or demonstrate a fresh live JEV success.

[Cursor compatibility research](CURSOR_API_COMPATIBILITY.md) confirms that a
Cursor-issued API key is not a direct replacement for the application's Groq
inference transport. Provider configuration was not changed.

## Latest correction: provider waits and renamed workspace

The working directory is now `D:\Projects\Praxis`. Refreshed the editable
installation with `uv sync --frozen --cache-dir .cache/uv --reinstall-package praxis`.
The old Windows `uvicorn.exe` launcher still embedded the former directory;
the startup script and README now use `python -m uvicorn` instead. Package imports
remain `praxis`. No credentials, JEV settings or dependency versions changed.

The user's failed run lasted 229 seconds and ended in a timeout before the
Analyst completed. A subsequent bounded diagnostic received HTTP429 with
`Retry-After: 654`. CrewAI 1.15.33's synchronous task timeout waits for its running
executor worker during cleanup; it cannot interrupt a long native retry sleep.
The recorded error had also incorrectly grouped timeouts with evidence failures.
See `artifacts/user-briefing-failure.json` and `provider-timeout-probe.json`.
Groq documents organization-level limits and retry headers in its
[rate-limit documentation](https://console.groq.com/docs/rate-limits).

The adapter now rejects retry waits above 60 seconds or the remaining run budget
without sleeping or sending another request. Short waits still honor the provider
hint. A shared 120-second cooperative budget spans Groq calls for both agents;
individual request timeouts are capped by remaining time. This is not a strict
wall-clock guarantee for every network condition or Python scheduling delay.
Cooldowns and timeouts have distinct sanitized errors. Mandatory evidence,
numeric-claim checks and human approval requirements remain enforced. Analyst
corrections are instructed to reuse already retrieved evidence.

| Latest check | Observed result |
|---|---|
| Full offline suite | 151 passed, six live cases deselected; 19.96s; `artifacts/praxis-timeout-offline-tests.xml` |
| Original-model live morning | One test passed, three unrelated cases deselected; 82.37s test duration; `artifacts/praxis-morning-live-tests.xml` |
| Accepted briefing | 78.64s application duration, three priorities (INC-001, OPS-003, FIN-001), one actual Analyst retrieval, both agent tasks completed |
| Model retained | groq/openai/gpt-oss-120b; no automatic model fallback |
| Restarted app | Health OK, frontend HTTP200, default school dataset and configured original model confirmed |
| JEV | No new requests; startup cache still verified, school evaluation still absent |

The accepted run is `artifacts/react-api-yfs-morning.json`. Its Chief corrected a
numeric-prose rejection within the existing bounded retry before the final
validation passed. An alternative gpt-oss-20b experiment failed on cooldown and
numeric-prose checks; it was not selected. Those failures remain separately as
`groq-20b-first-failure.json`, `groq-20b-second-failure.json` and their XML files.
The live check is a measured successful run, not a promise that future free-plan
quota or model outputs cannot fail. No additional browser screenshot pass was
needed for this backend-only correction; the unchanged UI's earlier captures are
documented below.

## School dataset revision — retained verification

**Current verdict: READY WITH LIMITATIONS for the school-founder Rules/Groq demo.**

The default React/API/CLI dataset is now `yfs_operations.json`: 28 fictional
education-operation records at 2026-10-30. Public Young Founders School offerings
informed the scenario; no internal school information was obtained. See
YOUNG_FOUNDER_RESEARCH.md and YFS_DATASET.md. The startup dataset and its verified
saved JEV response remain separate and unchanged.

| Current school revision check | Observed result |
|---|---|
| Full offline Python suite | 147 passed, zero failures/errors, five live cases deselected; 18.74s; `artifacts/yfs-offline-tests.xml` |
| Agent checks after final team-label guidance | 8 passed, two live cases deselected; 8.56s |
| React/Vitest | 9 passed; `artifacts/yfs-frontend-tests.log` |
| TypeScript/Vite production build | Exit 0; rebuilt `frontend/dist` |
| Actual school morning through Chrome | Accepted, three priorities, genuine Analyst retrieval and both task outcomes; approximately 36.2s for that job |
| School explanation through API | 1 live test passed, two startup cases deselected; 106.77s test duration; `artifacts/yfs-explanation-live-tests.xml` |
| Browser workflow | 22 passing checks, ten screenshots, one briefing POST in the successful rehearsal, zero JEV calls and uncaught browser exceptions |
| Independent visual review | Ship for supplied desktop/mobile and workflow captures; no material visible defect |
| Design documentation check | Existing design remains appropriate; no material drift or token changes |
| School JEV | Not live-evaluated; zero additional JEV requests made for this revision |
| Preserved startup JEV | Read-only API readiness check confirms saved INC-001 response still matches; school readiness correctly shows no matching cache |

Current browser evidence is `artifacts/rehearsal-yfs/report.json`, ten named PNGs,
and `run-result.json`. The accepted morning prioritized INC-001, OPS-001 and
CAN-001. Exact metrics are INR 300,000.00 signed agreement exposure, INR 340,000.00
potential partnership pipeline, 13 issues, three overdue tasks, four school/sponsor
issue records and three proposals. Neither amount is donations received, realized
revenue or an expected loss. Rankings and prose outside mandatory policy can vary.

The comparison output is `artifacts/react-api-yfs-explanation.json`. The test checks
real retrieval, both completed task events, correct money, a mandatory leading
incident, a proposed follow-up and an explicit FEAT-001 Analyst finding. Neither
this nor the source validator certifies every qualitative interpretation.

Two earlier school attempts failed and remain preserved. The first morning
attempt lacked agreement evidence in the Analyst handoff; the Chief correctly
rejected it. The handoff now requires each mandatory incident and its agreement
sources, with explicit correction feedback and the existing bounded retry.
Two regression cases cover missing incident and missing agreement. The first
explanation attempt encountered Groq rate limits and finally failed schema
validation on an invented Product owner. The final prompt explicitly supplies
allowed team labels and recorded owners; the subsequent live explanation passed.
No invalid owner was silently remapped and no rejected briefing was shown as
accepted. Failures are retained as `rehearsal-yfs/failed-report.json`,
`rehearsal-yfs/failed-run-result.json`, `yfs-explanation-first-failed.json` and
`yfs-explanation-first-failed-tests.xml`.

Commands for this revision (PowerShell, project root unless noted):

```powershell
.venv/Scripts/python.exe -m pytest -m 'not live' -q --disable-warnings --junitxml=artifacts/yfs-offline-tests.xml
.venv/Scripts/python.exe -m pytest tests/test_agents.py tests/test_crew_mocked.py -m 'not live' -q --disable-warnings
.venv/Scripts/python.exe -m pytest tests/test_live_react_api.py -k yfs --live -q --disable-warnings --junitxml=artifacts/yfs-explanation-live-tests.xml
# frontend directory, with the existing local Node on PATH
npm test
npm run build
# project root, backend on port 8000; makes one real Rules/Groq run
.tools/node-v20.18.0-win-x64/node.exe --experimental-websocket scripts/rehearse-desktop.mjs
```

For recording, open http://127.0.0.1:8000, hard-refresh, keep **YFS founder demo**
and **Rules**, then prepare a real briefing. The automated rehearsal's temporary
browser is closed; it does not prepopulate the user's tab. Use LOOM_DEMO.md for
the school-specific 90-second script. The saved JEV example remains under
**Startup demo / INC-001**; a new school evaluation would consume new usage.
Provider variability/rate limits, human interpretation review and local-only
approvals remain limitations. Loom recording itself has not been performed.

## Previous startup revision — retained historical verification

The following results apply to the preserved startup dataset, not the new school seed.

Both startup demo prompts completed real CrewAI runs on the enhanced JSON through
the API. Offline Python and React checks pass. The corrected JEV key passed
authentication and one genuine decision; its saved response is reused by the API.
The actual Chrome desktop rehearsal passes. JEV verification/comparison is scoped
to INC-001, not a bulk accuracy benchmark. Loom recording and speaking practice remain.

## Actual results

The original JEV failure was a credential/provider mismatch: an OpenRouter key
was sent to jev-ai.org, which returned HTTP401 `unknown_key`. After the user
replaced it, the uncharged models endpoint returned HTTP200 and listed jev-1.13.
One authorized live INC-001 decision then passed parsing and cache/API checks.
The backend was restarted to load the corrected key. See JEV_AUTH_DIAGNOSIS.md.

| Check | Observed result |
|---|---|
| Final offline Python suite | 139 passed, zero failures/errors; four live cases deselected; 27.62s; includes authentication diagnostics |
| React/Vitest DOM interactions | 8 passed, zero failures |
| TypeScript + Vite production build | Exit 0; compiled output in frontend/dist |
| Live morning through API | Accepted; 40.12s |
| Live explanation through API | Accepted; 103.52s; latest explanation pytest passed |
| Historical JEV recheck with original wrong-service key | HTTP401; preserved as prior failure evidence |
| Corrected-key JEV live check | 1 passed; genuine response saved and reused without another provider request |
| Baseline label fixture | Ten team-routing/urgency cases pass inside offline suite |
| Frontend HTTP smoke | Development server returned HTTP200 on 5173 |
| Actual Chrome desktop rehearsal | 21 checks passed; 10 screenshots visually reviewed; one Rules/Groq run, zero JEV calls |

Individual elapsed times include provider waits/corrections and are not latency
guarantees. Groq free-plan rate limits were observed. The combined live run first
passed morning and rejected explanation for a missing primary citation. After
making citation feedback/action guidance explicit, explanation passed separately
with one case deselected. `react-api-live-tests.xml` preserves that earlier
one-pass/one-fail run; `react-api-explanation-tests.xml` records the successful
retry. No failure was relabeled as passing.

The live-test amount assertion was also corrected to compare Decimal values:
`84000.00` and `84000` are numerically equal. This was a test representation issue,
not a financial calculation change.

## Evidence and test types

**Unit/data/policy:** parsing, duplicates, invalid/missing money and dates, exact
cohorts, deadline boundaries, exclusions, mandatory escalation, provider selection,
source scope, numeric prose, structured outputs, approval requirements and safe
errors. Validated Analyst limitations about retrieved evidence can reach global
briefing limitations, while priority eligibility remains restricted to findings.

**Offline integration:** actual two-agent CrewAI configuration and genuine tool
invocation; scripted BaseLLM sequential task context; FastAPI jobs/409/failures;
mocked Groq HTTP tool and JSON-object round trips with local Pydantic validation;
JEV choice/score/noul parsing, fractional scores, retries/timeouts/idempotency,
permanent errors, caching and explicit failure behavior. These mocks never ship
as live product output. Warnings in the suite originate from library deprecations
and CrewAI checkpoint/event behavior; the final run had no failed tests.

**React interaction tests:** exact cents, evidence dialog, pending request locks,
poll recovery, session-local approval/rejection with no extra network mutation,
offline recovery, explicit JEV request/provenance/fractional score display, menu
Escape/focus restoration. jsdom is not a browser screenshot or full accessibility
audit. The deprecated whatwg-encoding npm message did not block install/build/tests.

**Live Groq:** startup outputs are `artifacts/react-api-morning.json` and
`artifacts/react-api-explanation.json`. Each has completed status, live result,
both validated agent task events and actual Analyst retrieval. Morning priorities:
INC-001, CAN-001, REL-001.
Explanation evidence includes FEAT-001. Metrics are deterministic, including
USD 84,000.00 exposure and USD 172,000.00 potential pipeline. Existing original
Streamlit-era artifacts are historical and were not rewritten as current runs.

**Live JEV:** the corrected-key test passed (`artifacts/jev-corrected-key-live-tests.xml`).
The genuine saved result is INC-001, provider jev-ai.org, exact build
jev-1.13-20260917, request ID `dec_14499424bdea53337df1163b`. It returned Engineering,
Critical, fractional expected urgency 2.97/3 and customer-risk probability estimate
0.86. These estimates are not proven outcomes or business facts.

Reported usage was 1575 input tokens, 95 output tokens, zero charged tokens and
**one charged credit**, wallet credits. Provider-reported latency was 341ms, not
a measured comparison with Rules or Groq. The test replaced its provider request
method with a failure sentinel after the live result and verified cache reuse
plus the local comparison endpoint. A subsequent check of the restarted running
API returned HTTP200, `cached=true` and `live_verified=true`, with the same result.

Evidence: `artifacts/jev-live-verification.json`, `jev-live-comparison.json` and
`jev-decisions.json`. The original authentication-failure XML remains historical.
No bulk JEV fixture run or comparative accuracy/cost/speed claim is made. Preserve
the cache and use Founder demo / INC-001 for repeat viewing without new model calls.

## Reliability changes verified

The enhanced 28-record JSON retains source IDs/links, amounts and reference date.
Individual financial values/currencies now reach the compact Analyst snapshot.
Cents remain visible; prose references require declared evidence. Prompts preserve
conditional outcomes and authoritative financial missingness. A global-limitation
handoff bug and vague missing-primary citation feedback were fixed with tests.

Groq's schema-constrained decoder repeatedly returned empty-generation errors.
The final adapter uses JSON object mode and the same local Pydantic models,
task guardrails and final evidence/policy checks. It keeps retrieval separate from
final output, with a 4000-token output cap. No schema or policy validation was
removed. Auth/request failures remain explicit; rate-limit waits are bounded by
the existing CrewAI runtime. Real runs can still fail or take over a minute.

JEV evaluates only one selected record, batches three questions, and reuses a
genuine fingerprinted response cache when available. Cache errors fail closed;
permanent provider errors do not trigger a hidden rules fallback. Rules remain
the default. JEV can now be demonstrated with the verified cached INC-001 result;
other records/datasets may require a new charged request.

## Environment

Windows PowerShell; project Python 3.12.7. The local environment is
managed by uv. `uv.lock` and `frontend/package-lock.json` are the reproducible
resolution sources. Git was available during setup, but this folder has no Git
repository; no commit or push was performed.

| Python dependency | Actual installed version |
|---|---|
| crewai | 1.15.33 |
| streamlit | 1.66.1 |
| pydantic | 2.12.5 |
| pytest | 9.2.0 |
| httpx | 0.28.1 |
| python-dotenv | 1.2.4 |
| fastapi | 0.162.0 |
| uvicorn | 0.54.0 |

| JavaScript dependency | Locked installed version |
|---|---|
| react | 19.3.1 |
| react-dom | 19.3.1 |
| typescript | 5.9.3 |
| vite | 6.4.5 |
| vitest | 3.2.7 |
| jsdom | 26.1.0 |

The workspace uses local Node 20.18.0; a new machine can use normally installed
Node compatible with the locked Vite release. Credentials remain in ignored .env
or server environment. No VITE-prefixed provider credentials exist.

## Created / modified areas

- New `frontend/`: React/TypeScript workspace, authored responsive CSS, self-hosted
  font/Lucide, evidence drawer, records search, local reviews, JEV view, actual
  execution trail, API client, tests and npm lockfile.
- New `src/praxis/api.py`: local HTTP seam, typed requests, readiness, evidence,
  one-record decisions and single-worker briefing jobs; serves compiled React.
- New `data/synthetic/founder_demo.json`; original regression dataset retained.
- New JEV adapter and mocked fixtures/tests. Updated config, schemas, provider
  selection and briefing coordination for explicit one-record budget/cache scope.
- Updated agent guidance/Groq transport, evidence validation, legacy monetary
  display, CLI evaluation wording, Python dependency metadata and uv lock.
- Added/expanded `tests/test_api.py`, `test_demo_data.py`, `test_jev.py`,
  `test_review_fixes.py`, `test_live_react_api.py`, Groq and environment checks.
- Added frontend setup/start and backend start scripts. Updated .gitignore and
  .env.example. Refreshed README, PRODUCT, DESIGN, .impeccable/design.json and docs.

## Commands executed

```powershell
# Environment/dependency setup: official CrewAI/uv docs checked; user initial sync
uv sync --python 3.12
# Later FastAPI dependency sync / reproducible install
uv sync --cache-dir .cache/uv --no-managed-python --python "C:/Users/MY PC/AppData/Local/Programs/Python/Python312/python.exe"
# User setup script ran npm install successfully (162 packages)
# Final backend suite
.venv/Scripts/python.exe -m pytest -m "not live" -q --disable-warnings --junitxml=artifacts/react-backend-tests.xml
# Real HTTP seam and provider runs, explicit opt-in
.venv/Scripts/python.exe -m pytest tests/test_live_react_api.py --live -q --junitxml=artifacts/react-api-live-tests.xml
.venv/Scripts/python.exe -m pytest tests/test_live_react_api.py -k explanation --live -q --junitxml=artifacts/react-api-explanation-tests.xml
# Frontend directory, using workspace-local Node PATH
npm test
npm run build
```

Targeted regression runs and a budget probe preceded final checks. Bounded
temporary tests preserved the failed old-key check and verified the corrected
key with one successful decision. They are not in normal test discovery; a saved
attempt guard prevents automatic repeat spending if the cache is unavailable.

## Launch and rehearsal

The compiled React app can be served together with the API. In the user's own
terminal, stop any old backend and run:

```powershell
cd D:\Projects\Praxis
uv run --frozen --cache-dir .cache/uv python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and hard-refresh to load the new assets. Keep Rules
selected and use Prepare my briefing. Development frontend is also available
on 5173 while Vite runs; it proxies to the same API. README contains both launch
paths. The user's earlier log verified backend startup, static assets and overview
HTTP200. The sandboxed Python launcher was blocked. Approved execution outside
the sandbox subsequently started the backend successfully. It was running during
the final Chrome rehearsal; use the command above if it stops again.

Initial source-only independent review found contrast and closed mobile navigation
focus issues. Both were corrected; muted text is 5.23:1 on white / 4.96:1 on the
header. Initial Chrome rendering was blocked by sandbox permissions. Approved
outside execution later produced ten actual captures at desktop 1440×1000,
1366×768 and emulated mobile 390×844. The browser completed a real briefing,
source inspection, search, local approval/rejection and execution review. All
21 checks passed, with exactly one briefing POST, no JEV requests and no uncaught
browser exceptions. An independent reviewer inspected all ten captures and
returned **ship for the viewed captures**, finding no material visible defect.
This does not certify full WCAG, screen-reader or physical-device behavior.
Evidence: `artifacts/rehearsal/report.json` and its ten named PNGs.
Design documentation was completed in-thread after its documenter agent hit its
usage limit. No raster artwork ships in the product; rehearsal PNGs are artifacts.

Use LOOM_DEMO.md for the 90-second segment and 3–5-minute expansion. Rehearse
speaking pace and provider timing. Those human checks remain. The local app has
no authentication, durable queue, real connectors or automatic external actions;
browser refresh loses local approvals. Semantic accuracy still needs human review.
