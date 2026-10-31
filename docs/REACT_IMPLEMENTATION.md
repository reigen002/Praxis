# React dashboard and JEV implementation

User-approved scope: replace the simple primary interface with an attractive
React dashboard, improve the synthetic JSON demo, implement optional JEV, and
resolve the review findings. Preserve the working Streamlit entry point.

Architecture: React + TypeScript + Vite and authored CSS, with Lucide icons.
A small FastAPI service exposes the existing Python tools and CrewAI service.
Model keys remain on the server. Background runs are polled; only actual states
and recorded events are displayed. Review decisions stay local to the browser.

- [x] Fix financial snapshot/prose evidence gaps and conditional outcome wording.
- [x] Add a richer, coherent 28-record founder demo JSON with fixed reference date.
- [x] Implement documented JEV choice/score/noul parsing, bounded retries,
  idempotency, model pinning and mocked tests. Preserve fractional scores.
- [x] Expose health/readiness, datasets, records/metrics, decisions and real run jobs.
- [x] Build the responsive React workspace, evidence drawer, review queue,
  decisions view and actual execution activity.
- [x] Lock/install dependencies, test backend/frontend, build React, verify live
  Groq and JEV only when configured; update launch and recording instructions.

Ruling: use FastAPI because a separate browser client now requires an HTTP seam;
no database, external integrations, message sending or account system is added.
Ruling: JEV errors are explicit; rules stay the default and are never a hidden
fallback. Comparison views require verified live JEV results.

## Direction contract

THESIS: an operating desk for a founder making the morning's decisions. Priorities
and their evidence occupy the workspace; charts never stand in for real data.

OWN-WORLD: ink navy navigation, pale stone canvas, white working surfaces, indigo
actions, amber attention and red critical states. Humanist sans typography and
tabular financial figures; subtle borders and deliberate whitespace.

STORY: scan business health, ask a question, inspect the ranked briefing and
source record, then review a follow-up. Uncertainty and provider readiness are visible.

FIRST VIEWPORT: fixed slim sidebar, a restrained top utility bar, a large greeting
and dataset date, a horizontal financial/operations strip, a wide founder prompt,
and a two-column briefing/work-queue area. The run button is the primary action.

FORM: code-led Operate surface. A calm command desk with a persistent source
drawer is chosen from the existing product's workflow; the unavailable Impeccable
engine has no seed key. Native browser controls remain accessible.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Verification scope

React production build and eight DOM interaction tests pass. Source-only finish
review found small-text contrast and hidden mobile navigation focus defects;
both were corrected. Muted text now measures 5.23:1 on white and 4.96:1 on the
table header. Approved real-Chrome rehearsal subsequently passed all 21 checks
and produced ten screenshots. Independent visual review returned ship for those
captures: desktop 1440×1000/1366×768 and an emulated mobile overview at 390×844.
There were no material visible defects, no uncaught browser exceptions and no
JEV calls. This is not a full accessibility or physical-device certification.
Design documentation was completed in-thread after the documenter agent hit its
usage limit. No raster artwork ships in the product.

JEV adapter/mock tests and corrected-key live verification pass. The old key was
an OpenRouter credential and returned HTTP401. The corrected key produced one
genuine INC-001 result, saved for reuse; the running API returns it as cached.
One credit was reported as used. No bulk benchmark was run. Exact evidence and
remaining scope limits are recorded in VERIFICATION.md.
