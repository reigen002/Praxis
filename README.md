# Praxis — AI Chief of Staff

Praxis turns operational updates into a sourced founder briefing. Its default
demo is a fictional education programme inspired by Young Founders School's public
school partnerships, internships, mentoring and corporate programmes.
A real CrewAI Analyst retrieves business records; a Chief of Staff proposes
priorities, owners and follow-ups. Python owns arithmetic, deadlines and mandatory
escalation. React makes the evidence inspectable.

**SYNTHETIC DEMONSTRATION DATA.** No email, CRM or external action endpoints exist.
Approvals change local browser state and reset when the page or run changes.

## Install

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 20.18+ and npm.
Windows PowerShell is tested. Git is optional for running this folder.

```powershell
cd D:\Projects\Praxis
$env:UV_CACHE_DIR = "$PWD\.cache\uv"
$env:UV_PYTHON_INSTALL_DIR = "$PWD\.tools\python"
uv sync --frozen --python 3.12
cd frontend
npm ci
cd ..
```

For this workspace, `scripts/setup-frontend.ps1` also detects the existing local
Node installation. On a fresh machine install Node normally. `uv.lock` and
`frontend/package-lock.json` pin dependency resolutions.

After moving or renaming an existing project folder, refresh its editable Python
installation with `uv sync --frozen --cache-dir .cache/uv --reinstall-package praxis`.
The launch commands below use Python modules so moved Windows console launchers
cannot retain the previous folder path.

Copy `.env.example` to `.env` **only if `.env` does not already exist**. Edit it
privately. Keys belong on the server, never in React files or chat.

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your-private-groq-key
GROQ_MODEL=openai/gpt-oss-120b
DECISION_PROVIDER=rules
JEV_API_KEY=
JEV_RECORD_ID=INC-001
```

Requests for this model go to Groq with a Groq key; the `openai/` prefix identifies
the model publisher. OpenAI and Anthropic are also supported using their own
variables in `.env.example`. Provider access, model tool support and quota affect
runs. Detected credentials are not a connectivity check. Existing shell variables
take precedence over `.env`; restart the backend after editing credentials.

## Launch React and Python

Backend, in one terminal:

```powershell
cd D:\Projects\Praxis
uv run --frozen --cache-dir .cache/uv python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8000
```

Frontend, in another terminal with normally installed Node:

```powershell
cd D:\Projects\Praxis\frontend
npm run dev
```

For this workspace's existing local Node, use `scripts/start-frontend.ps1` or
these script-free commands if PowerShell blocks `.ps1` files:

```powershell
cd D:\Projects\Praxis\frontend
$env:PATH = "D:\Projects\Praxis\.tools\node-v20.18.0-win-x64;$env:PATH"
& '..\.tools\node-v20.18.0-win-x64\node.exe' 'node_modules\vite\bin\vite.js' --host 127.0.0.1
```

Open **http://127.0.0.1:5173**. API health: http://127.0.0.1:8000/api/health.
Keep terminals open; Ctrl+C stops them. `scripts/start-backend.ps1` wraps the
backend command when scripts are allowed.

Alternatively run `npm run build` in `frontend`, then start/restart the backend
and open http://127.0.0.1:8000. FastAPI serves `frontend/dist` when it exists at
startup. The original Streamlit UI is retained separately: `uv run --frozen
python -m streamlit run app.py`. Use React for the redesigned demo and JEV.

## Use it

1. Keep **YFS founder demo** selected. The initial KPIs and **Rules overview** are
   deterministic; no agent briefing is shown before an actual run.
2. Click **Prepare my briefing**. Exactly two sequential CrewAI agents execute.
   Output failing evidence/policy checks is withheld.
3. Open source ID buttons to inspect records, deadlines and related evidence.
4. Open **Follow-up review**, then approve or reject locally. Neither sends mail.
5. Open **Execution activity** for actual tool completions, agent outcomes and
   validations. No fabricated progress steps or private reasoning are displayed.
6. Use **Cohort vs. redesign** for a second real CrewAI run comparing the urgent
   cohort access issue against an optional certificate preview redesign.

The default JSON is `data/synthetic/yfs_operations.json`: 28 linked records,
reference date **2026-10-30**. It covers cohort onboarding, mentor cover, host
project briefs, school renewals, sponsor proposals, impact reporting, routine
communications and completed work. All counterparties, amounts and incidents are
invented; none is a report of an actual Young Founders School problem. Public
offerings and inferred day-to-day needs are distinguished in the
[research notes](docs/YOUNG_FOUNDER_RESEARCH.md); the [dataset guide](docs/YFS_DATASET.md)
explains the fictional operating day and metric definitions.

**Startup demo** retains `data/synthetic/founder_demo.json` and its saved genuine
JEV decision unchanged. **Original regression** retains `updates.json`. The React
app, API and CLI default to YFS; legacy Streamlit retains its original dataset.

| Deterministic measure | Value |
|---|---:|
| Programme agreement exposure | INR 300,000.00 |
| Potential partnership pipeline | INR 340,000.00 |
| Open issues | 13 |
| Overdue internal tasks | 3 |
| School or sponsor issue records | 4 |
| Programme proposals awaiting action | 3 |

Definitions and exact eligible source cohorts appear in the metric drawer.
Exposure is signed agreement face value, not expected loss, donations received or
realized revenue. Unsigned proposal pipeline is separate. Decimal arithmetic
preserves cents; missing financial data stays
missing. `INC-001` must lead at Critical urgency with `CON-001` cited. Other
rankings and generated wording vary.

## JEV with limited usage

For the repeatable test drive, follow [TEST_DRIVE.md](docs/TEST_DRIVE.md), then
the [four-minute recording script](docs/LOOM_DEMO.md). **Open saved briefings**
reopens accepted real CrewAI runs with historical provenance and no new inference.
**Prepare my briefing** always performs a fresh live execution and saves accepted
results. Records, metrics, policy and agent events are rechecked before reopening;
changed datasets do not silently reuse a previous result. Reviews remain local.

Prepared runs are ignored local files under `artifacts/saved-briefings`, not
bundled fixtures or simulated output. A new checkout must complete real runs
before this panel contains anything. This workspace's existing genuine school
exports were imported using `uv run --frozen python scripts/prepare-demo.py`.
That import script requires the original completed rehearsal exports and makes
no provider calls. The saved startup JEV button uses a read-only cache endpoint.

The saved verified decision belongs to **Startup demo / INC-001**. Select that
dataset and use **View saved live decision** to reuse it without another JEV
request. The new school evidence has a different cache fingerprint and has **no
accepted saved JEV answer**. Keep **Rules** on YFS to preserve credits. Selecting
JEV for new evidence makes a new provider request; the old result is never reused
as a school decision. Changing datasets resets the selected provider to Rules.

Rules remain the default. JEV is optional and does not block startup. Set
`JEV_API_KEY` privately and restart the backend. The adapter follows the
[official API](https://jev-ai.org/docs/) with model `jev-1.13`, recording its exact
returned version.

Use a full key created at [JEV API key settings](https://jev-ai.org/settings/apikeys/).
An OpenRouter key authenticates with a different service and is rejected before
this adapter sends a decision request. See [the authentication diagnosis](docs/JEV_AUTH_DIAGNOSIS.md).

- At most one selected record per briefing, default `INC-001`. Other records
  explicitly use rules-v1. No bulk JEV evaluation runs automatically.
- One decision request batches responsible-team choice, urgency score and
  customer-relationship-risk probability. Fractional expected scores are preserved.
- Successful genuine responses are saved in ignored `artifacts/jev-decisions.json`,
  keyed by model, questions, complete record/related evidence and reference date.
  Repeat views/runs reuse matching responses and say **Saved live decision**.
- Keep this cache and the demo JSON unchanged for recording. Selecting another
  record or changing evidence can spend another call. Three questions in one
  HTTP request may still consume provider-metered question/token allowance.
- Bounded retries reuse an idempotency key. Auth, request and spend-limit errors
  are not retried. Long Retry-After hints stop the request rather than retrying
  early. Corrupt caches fail closed before spending again.
- Request identifiers are saved before sending, so interrupted requests reuse
  their key after a restart. Once an unresolved original request ID is known,
  subsequent clicks only read its status. The answer wait is bounded at 30 seconds
  per attempt, with a 5-second connection timeout.
- JEV's status endpoint returns metadata, not lost answers. A completed request
  can have used credit even when its answer never reached this app. Do not clear
  request tracking to retry blindly; use Rules or the saved Startup demo decision.
  See [request recovery](docs/JEV_REQUEST_RECOVERY.md).
- If saving a successful result fails, the error says **Do not retry a paid
  decision**. Resolve storage before repeating. No hidden rules fallback occurs.

The comparison view appears only after a real/saved provider result. Mocked
responses exist only in tests. Probabilities are model estimates; baseline scores
have no calibrated confidence. Mandatory escalation always wins. One comparison
is not an accuracy benchmark. No superiority, comparative speed or cost claim is
made. See [actual verification](docs/VERIFICATION.md) for current live status.

## Architecture and limitations

```text
React / TypeScript → local FastAPI → application service
JSON → Pydantic → deterministic tools + optional decision signals
CrewAI Analyst → validated task context → Chief of Staff
Validated briefing + exact metrics + actual events → React / local review
```

Native CrewAI Python APIs, exactly two agents, sequential tasks, Pydantic output
and guardrails. No LangGraph/LangChain layer, database or external connectors.
Agents cannot delegate or execute arbitrary code. Source validation rejects
unknown, unretrieved and undeclared sources, numeric prose claims and downgraded
mandatory incidents. Exact numbers come from deterministic UI fields.
Qualitative interpretations still require human review: valid citations do not
prove semantic entailment.

This is a single-user loopback demo, with one briefing at a time and up to 20
in-memory jobs. It has no authentication or durable queue. Restart loses job
status; refresh loses local approvals. Do not expose it publicly. Events appear
after completion/failure; private reasoning is never streamed. Groq limits can
delay or fail a run. Groq calls share a 120-second cooperative time budget, with
request timeouts capped by the remaining budget. Retry-After waits exceeding 60
seconds, or the remaining budget, stop immediately with a cooldown message.
Agent and network timeouts are reported separately from evidence rejection.
Missing providers produce honest errors, never canned output.

## Checks

```powershell
uv run --frozen python -m pytest -m "not live" -q
cd frontend
npm test
npm run build
cd ..
# Explicit opt-in: actual LLM usage
uv run --frozen python -m pytest tests/test_live_react_api.py --live -q
# School comparison only (one additional real run)
uv run --frozen python -m pytest tests/test_live_react_api.py -k yfs --live -q
# Original two prompts, additional LLM usage
uv run --frozen python -m pytest tests/test_agents.py -m live --live -q
uv run --frozen python -m praxis check
uv run --frozen python -m praxis evaluate
```

The CLI defaults to the school dataset; append `--dataset demo` for the startup
scenario. The school's ten-case label fixture tests team routing and urgency regression; it is not
independent accuracy evidence. No live bulk JEV benchmark runs. Coverage includes
data, duplicates, missing money, metrics, boundaries, rules, real CrewAI tool/task
configuration, mocked orchestration, JEV protocol/errors/cache, sources, approval
and React/API behavior. Unit/mocked tests are separate from opt-in live tests.

Core versions: Python 3.12.7, CrewAI 1.15.33, Pydantic 2.12.5, httpx 0.28.1,
pytest 9.2.0, FastAPI 0.162.0, Uvicorn 0.54.0, Streamlit 1.66.1. JavaScript
versions are recorded in `frontend/package-lock.json`.

- [Architecture](docs/ARCHITECTURE.md)
- [Decisions](docs/DECISIONS.md)
- [90-second Loom runbook](docs/LOOM_DEMO.md)
- The runbook also includes a real-Chrome rehearsal helper that saves local
  screenshots, checks the UI, and makes at most one Rules/Groq run with JEV blocked.
- [Tests and live verification](docs/VERIFICATION.md)

Official references: [CrewAI docs](https://docs.crewai.com/),
[CrewAI source](https://github.com/crewAIInc/crewAI),
[uv](https://docs.astral.sh/uv/), [JEV](https://jev-ai.org/docs/).
