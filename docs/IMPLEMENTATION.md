# Praxis implementation checkpoints

> Historical Streamlit-first milestone plan. The user subsequently authorized a
> React redesign, a FastAPI seam and JEV implementation. Current implementation
> and verification are in REACT_IMPLEMENTATION.md and VERIFICATION.md; the JEV
> deferral and no-backend statements below describe the earlier build only.

User specification: the Praxis build request supplied in this session.
Native Python CrewAI, Streamlit, Pydantic, pytest, httpx; no backend server,
LangChain, external mutations, commits, or pushes. Reference date is fixed.

- [x] M0: Python 3.12 local uv environment; resolve lock; import real CrewAI.
- [x] M1: validated synthetic dataset, Decimal money, explicit metric cohorts,
  deadline and escalation tools. Verify boundaries, duplicates and totals.
- [x] M2: exactly two sequential agents, native tools, Pydantic task outputs,
  source guardrails and validated task context. Attempt a real provider run.
- [x] M3: dashboard implemented; AppTest covers loading, disabled provider and local review. Browser visual rehearsal remains outstanding.
- [x] M4: malformed outputs, provider failures and offline integration tests.
- [ ] M5: optional JEV only after core verification; documented protocol,
  mocked parser checks, explicit unavailable status, live comparison only if verified.
- [x] M6: frozen install, complete test suite, demo prompts, 90-second runbook,
  environment report, limitations and truthful readiness verdict. Documents are
  written and live/UI checks pass; desktop visual rehearsal and recording remain manual.

Code boundaries: schemas.py owns contracts; data/ owns parsing; tools/ owns
retrieval and arithmetic; decisions/ owns bounded judgment; agents/ owns CrewAI;
validation/ owns evidence policy; services/ coordinates runs; app.py owns local UI.
Every milestone adds its relevant tests before implementation, runs checks and
records evidence. Existing provider configuration is used without exposing secrets.

## Observed status

Both real Groq scenarios pass using `openai/gpt-oss-120b`. The user configured the
key privately in ignored `.env`. An earlier inherited local gateway failed and
is unused. Groq compatibility fixes cover zero-argument tool schemas, provider
wait hints and the explicit tool-to-structured-output handoff. A compact snapshot
reduces repeated tool history. Source validation permits legitimate analyst
comparisons and known record identifiers while rejecting unknown references,
unsupported numeric prose and invalid priority categories. M5 remains disabled.

Latest offline command: `.venv/Scripts/python.exe -m pytest -m "not live" -q
--disable-warnings --junitxml=artifacts/offline-tests.xml` — 48 passed, 2 deselected.
Live scenario command: `.venv/Scripts/python.exe -m pytest tests/test_agents.py
-m live --live -q -x --tb=short --disable-warnings --junitxml=artifacts/live-tests.xml`
— 2 passed. Additional one-time Streamlit checks using actual saved live output
passed both scenarios' rendering and local review buttons. No commits or pushes
were made. See VERIFICATION.md.

Groq provider support was added after the user requested a free API option.
Existing dependencies suffice. Mocked HTTP/native tool and real provider tests
pass. A Cursor-issued key is not a
replacement for a provider API key.
