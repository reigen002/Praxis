# Desktop rehearsal — school founder scenario, Rules/Groq

## Current verification boundary

**School rehearsal completed on 2026-10-30.** The default is now YFS founder demo:
28 fictional school/mentor/partner records, fixed date 2026-10-30 and INR metrics.
The records are informed by public programmes, not obtained from YFS's operations.
See YOUNG_FOUNDER_RESEARCH.md and YFS_DATASET.md.

The actual Chrome flow passed: school dataset/KPIs, loaded self-hosted font,
desktop layouts at 1440×1000 and 1366×768, emulated mobile at 390×844, keyboard
menu dismissal, metric definitions, a real Rules/Groq briefing, incident/contract
evidence, feature search, local approval/rejection and actual execution events.
Exactly one briefing POST occurred, with zero JEV requests and zero uncaught
browser exceptions. No external message was sent.

All **22 checks** passed. Ten screenshots and `artifacts/rehearsal-yfs/report.json`
record the result; `run-result.json` preserves the accepted live output. Its
priorities were the cohort access incident, mentor coverage, and possible host
intake pause. The morning job took about 36.2 seconds; this is an observed run,
not a latency guarantee.

Both the main agent and an independent visual reviewer inspected the captures.
The review disposition was **ship for the viewed captures**, with no material
visible layout/readability defect. No UI edits were needed after capture.
This is not full WCAG, screen-reader or physical-device verification.

The first school attempt failed correctly: the Analyst omitted contractual
evidence needed by the Chief. The task handoff now requires each mandatory
incident and its agreement sources before context reaches the Chief. Regression
tests cover missing incident and missing contract cases. The initial report and
failed output remain as `failed-report.json` and `failed-run-result.json`; they
were not relabeled successful. Prior startup screenshots remain in
`artifacts/rehearsal` and do not represent the new seed.

For another rehearsal, run `scripts/rehearse-desktop.mjs` from normal PowerShell
with the backend open, as documented in LOOM_DEMO.md. It makes at most one new
Groq briefing request; JEV routes remain blocked. No JEV credentials were changed.

## Recording setup

Use the compiled React app at http://127.0.0.1:8000 with the current backend open.
Maximize the browser, close unrelated tabs and use a readable zoom. Select **YFS
founder demo** and **Rules**. Keep a successful live result in your tab; refreshing
clears it. The automated rehearsal uses a separate temporary browser profile.
Show a prepared result as prepared, or allow real provider latency on screen.

## Three-to-four-minute speaking rehearsal

| Time | Action | Narration |
|---|---|---|
| 0:00–0:20 | School demo and synthetic indicator | “I researched Young Founders School's public programmes and created a fictional operating day around cohorts, mentors and partnerships. These aren't their internal records.” |
| 0:20–0:40 | KPIs and metric definitions | “Python separates signed programme agreement exposure from unsigned partnership proposals. Neither is cash received, expected loss or recognized revenue.” |
| 0:40–1:40 | Start the morning briefing, or identify an already prepared run | “The Analyst retrieves real source records through CrewAI tools. The Chief receives validated findings and proposes priorities. Provider waits are real.” |
| 1:40–2:15 | Cohort access incident, agreement and conflicting notes | “Learner onboarding access is unresolved before kickoff and a school renewal review. An administrator's successful check does not confirm learner access. The founder needs an owner and verified recovery.” |
| 2:15–2:40 | Search FEAT-001 and inspect its deadline | “The certificate preview redesign has no committed deadline or contractual promise. Readiness takes priority; the final recommendation is still a judgment.” |
| 2:40–3:05 | Follow-up review, approve locally | “The founder inspects the proposed message. Approval changes only local state; no email is sent and no CRM record is modified.” |
| 3:05–3:35 | Actual execution events and source links | “These are recorded tool completions and agent outcomes. Pydantic and source checks gate the output; the interface does not fabricate agent steps.” |
| 3:35–3:55 | Limitations; optional separate Startup demo JEV segment | “This school run uses rules. JEV has a saved live evaluation for the separate startup example. I keep those results separate and preserve credits. Human review is still necessary.” |

For a strict 90-second segment, use the shorter plan in LOOM_DEMO.md and present
a previously prepared real briefing honestly. Do not run both prompts back-to-back
during that segment: observed provider waits can exceed its entire duration.

## Claims to keep precise

- A customer requesting a recovery plan before a discussion does not establish a
  contractual requirement that renewal depends on restoration. Treat such model
  wording as an inference requiring review. Narrate the actual source deadline,
  unresolved incident and mandatory escalation rule instead.
- Contract exposure and pipeline are not realized revenue or guaranteed losses.
- Rules scores are heuristics, not probabilities. The live JEV result is verified
  only for INC-001 on **Startup demo**, not the new school seed. Its probabilities
  remain model estimates. Changing datasets clears the current briefing/reviews,
  so show that optional example last.
- Local approval is neither message delivery nor an external action authorization.
- A screenshot proves rendering at its captured viewport, not every browser,
  physical device, accessibility requirement or qualitative model claim.

## Final human pass

Read the main question and KPI labels at recording zoom. Confirm no clipped
controls or horizontal desktop scrolling. Open/close evidence with mouse and
Escape. Read the draft before approving it. Practice the source-based explanation
without implying contractual dependencies absent from the records. Record only
after the browser captures and these human checks have been reviewed.
