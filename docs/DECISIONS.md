# Architecture decisions

1. **Native CrewAI Python APIs.** They integrate directly with Pydantic, custom
   tools and sequential validated task context. No LangGraph/LangChain is added.
2. **React plus a thin FastAPI seam.** The original Streamlit-only app worked,
   but the requested custom React interface needs HTTP. Reuse the same Python
   service rather than a second business implementation or separate database.
   Streamlit remains a legacy entry point.
3. **Two agents.** Analyst retrieves/interprets; Chief prioritizes and drafts.
   More specialists/delegation would add latency and recording risk.
4. **Deterministic financial facts and policy.** Decimal, distinct contract IDs,
   explicit cohorts and policy checks keep arithmetic and hard constraints outside
   the model. Numbers appear in source/KPI fields, not generated prose.
5. **Fixed dataset reference dates.** Rehearsal and recording see identical
   deadline calculations. The YFS-inspired school seed uses 2026-10-30; preserved
   startup datasets retain 2026-10-29 and their original amounts/links. This
   keeps the genuine saved startup JEV result valid without applying it to the
   new school evidence. Dataset changes reset the UI decision provider to Rules.
6. **Rules default; JEV optional.** JEV supplies decision signals only. It never
   writes the final briefing, calculates money or overrides mandatory policy.
   Different uncertainty semantics remain explicit.
7. **One-record JEV budget and persistent cache.** Batch three questions in one
   request, save genuine responses and reuse matching evidence/model/questions.
   This supports the user's limited allowance. No automatic bulk benchmark or
   forced-refresh control is added. Cache failures stop instead of spending again.
8. **Honest measured comparison.** One real JEV result can be compared with its
   rules signal, but cannot establish accuracy/cost/latency superiority. Mocked
   fixtures stay in tests. Live failures remain visible with no hidden fallback.
9. **Single-worker in-memory jobs.** This avoids blocking the browser during a
   real CrewAI run without introducing Redis/Celery or a durable job platform.
   Restart recovery is limited to an explicit missing-job error.
10. **Local approval only.** Browser state records approve/reject per run. No
    messages, CRM changes, external action endpoint or connector is implemented.
11. **Explicit provider routing.** Groq uses its own key and endpoint, retains
    namespaced model IDs and separates tool use from final structured outputs.
    Provider-compatible gateways are configurable, never assumed or required.
12. **Source scope is a guardrail, not proof.** Structural, ID, numeric and policy
    validation reject many unsupported claims. Conditional language and human
    review remain necessary for qualitative interpretations.
13. **Authored CSS and Lucide.** The dashboard needs consistent readable controls,
    evidence and state visibility. React/TypeScript/Vite, self-hosted DM Sans and
    a small icon library satisfy that without another component framework.
14. **Groq JSON object mode with local schema enforcement.** Repeated live
    schema-constrained generation failures consumed quota without producing
    output. JSON object mode retains native tool calls and explicit Pydantic
    task models, with validation in Python before context/output is accepted.
    It makes no provider-side schema-adherence guarantee. Output is bounded at
    4000 tokens; unsupported records, numbers and policy violations still fail.
