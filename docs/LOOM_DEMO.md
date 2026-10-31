# Praxis — rehearsal and recording

Start with [the exact test drive](TEST_DRIVE.md). The repeatable path uses genuine
saved executions, clearly labeled in the UI, and makes no new model calls.

## Recommended 4-minute recording

| Time | Click / show | Suggested narration |
|---|---|---|
| 0:00–0:25 | YFS founder demo; synthetic label; KPI definitions | “This operating day is fictional, inspired by Young Founders School's public programmes. Python computes the metrics and keeps contracted exposure separate from potential pipeline.” |
| 0:25–0:55 | Open saved briefings → Open morning briefing | “The Analyst retrieves evidence and passes validated findings to the Chief of Staff. This is their saved real execution; its original duration and activity are retained. The live-run button remains available.” |
| 0:55–1:35 | INC-001 → CON-001; related notes; assumptions | “The learner portal incident threatens an approaching partner renewal. Mandatory policy requires escalation. The conflicting notes prevent treating an admin success report as proof that learners can log in.” |
| 1:35–2:00 | Business updates; search FEAT-001, then CAN-002 | “The certificate redesign has no committed deadline. Missing financial evidence stays unknown rather than becoming zero. These are the underlying source records.” |
| 2:00–2:30 | Follow-up review; Copy draft; Approve locally; Reject | “The Chief proposes an owner, action and draft. I can inspect and review it, but no email is sent and no external record changes.” |
| 2:30–2:55 | Execution activity; Overview → Export briefing | “This trail records the original tools, records and completed agent tasks. I can export that execution for review.” |
| 2:55–3:20 | Open saved briefings → Open decision explanation | “This separate run explains the deadline and service-risk comparison. Facts, model judgments and missing information stay distinguishable.” |
| 3:20–3:55 | Startup demo → Decision lab → View saved live decision | “JEV is optional. This saved startup example routes to Engineering, scores urgency at a fractional expected value, and estimates relationship risk. These are model estimates, not certainty. Viewing it makes no new evaluation.” |
| 3:55–4:10 | JEV provenance and limitations | “The founder owns the decision. This is synthetic data, saved runs are labeled honestly, and fresh execution still depends on provider availability and quota.” |

Do the same sequence twice before recording. Switching datasets clears the current
view and local review state; reopen saved school runs to return to them. Fresh
successful runs are saved automatically. Do not clear `artifacts/saved-briefings`
or `artifacts/jev-decisions.json` before the recording.

If you want to show a fresh run in the video, start **Prepare my briefing** with
Rules first, inspect the source data while it runs, then show the accepted result.
Allow its actual duration; do not represent edited-out waiting as instant execution.
The prepared saved walkthrough is the dependable alternative if quota is unavailable.

## Real-browser rehearsal helper

With the current backend running on port 8000, run from a normal PowerShell
terminal in the project directory:

```powershell
& .\.tools\node-v20.18.0-win-x64\node.exe --experimental-websocket .\scripts\rehearse-desktop.mjs
```

Add **`--saved`** to rehearse the complete prepared walkthrough, including saved
explanation, JSON export and saved JEV, with fresh inference routes blocked. Its
report and captures are in `artifacts/rehearsal-praxis-saved`. The default command above
still performs one fresh Rules/Groq run.

With normally installed compatible Node, use `node --experimental-websocket
scripts/rehearse-desktop.mjs`. The helper uses installed Chrome with a separate
profile, without changing browser sandbox settings or your normal profile. It
checks desktop viewports 1440×1000 and 1366×768 plus an emulated 390×844 mobile
viewport. It saves captures and `artifacts/rehearsal-praxis-live/report.json`, checks sources,
search, native dialogs, local approval/rejection and actual execution events.

It makes at most one real Groq briefing request through the UI. Rules must be
selected; JEV decision routes are blocked for this rehearsal. It never sends a
message. A failed provider run is recorded honestly and is not automatically
resubmitted. `--preflight` checks readiness without launching Chrome or invoking
agents; it does not count as a browser rehearsal. Normal unit tests do not run
this helper. Browser captures still need visual inspection and narration practice.

Use normal PowerShell with the backend open. See DESKTOP_REHEARSAL.md for the
observed result. A repeat makes another Groq request. The prior startup captures
remain in `artifacts/rehearsal`; the helper now targets the school dataset.

## Before recording

Follow README launch commands: build React and serve it with the API on 8000,
or run the development frontend on 5173. Maximize the browser and use a readable
zoom. Keep **YFS founder demo** and **Rules** selected.
Check the synthetic label, fixed date and exact KPIs. Open the saved morning
briefing. Refresh clears the current view; the saved result can be reopened.
A prepared real run must be described as prepared, never as an instantaneous new execution.

JEV has a verified saved response for **Startup demo / INC-001**, not for the new
school seed. Keep Rules for the school recording to preserve the allowance.
For an optional longer JEV segment, finish showing the school briefing first,
then select Startup demo and open Decision lab / INC-001 / **View saved live
decision**. Explain that this is a separate startup example. Changing datasets
clears the current briefing and locally reviewed drafts, so do this last.

The saved startup score is 2.97/3 with a risk estimate of 86%. Its live check used
one credit; repeat views were verified as cached. Preserve ignored
`artifacts/jev-decisions.json` and `founder_demo.json`. They must match; a fresh
checkout does not include the cache. Never imply that result evaluates the school
records. A new school JEV evaluation would spend a new request and is not needed
for this demonstration. See VERIFICATION.md for precise live status.

## Exact prompts

Morning: “Prepare my founder briefing for today. What are the three most important
issues, and why?”

Explanation: “Why is the cohort access issue more urgent than the certificate preview redesign?”

The prepared explanation can be opened under Saved briefings. Submitting its
question through Prepare my briefing performs another real CrewAI run. For a
tight 90 seconds, show the prepared morning result and inspect the two records.

## Short 90-second option

| Time | Display / action | Say |
|---|---|---|
| 0–12s | YFS founder demo, fictional context, reference date and KPIs | “I researched Young Founders School's public programmes and built a fictional operating day around cohorts, mentors and partners. Python calculates these figures.” |
| 12–28s | Prepared real briefing and leading priority | “Two actual CrewAI agents run sequentially. The Analyst retrieves records, then the Chief proposes priorities through validated task context.” |
| 28–44s | Open INC-001 then CON-001 and conflicting linked notes | “Learner onboarding access is unresolved before a cohort kickoff and school renewal review. Policy requires escalation. The admin check does not prove learner access works.” |
| 44–56s | Business updates search FEAT-001, inspect source | “The certificate preview redesign has no committed deadline. Delivery readiness takes priority; the recommended response remains a judgment.” |
| 56–70s | Follow-up review; approve locally | “This is a proposed message. Approval only changes local state. No email or CRM actions occur.” |
| 70–82s | Execution activity | “These are actual recorded tools and task outcomes, with source IDs. The interface doesn't invent agent progress.” |
| 82–90s | Return to briefing and limitations | “These school records are invented, and the founder reviews every proposed action. JEV is optional; this run uses rules and keeps the saved startup evaluation separate.” |

For a longer recording, add the separate saved JEV example after this sequence.
Never describe mock results as live or valid source IDs as proof of every interpretation.

## Deterministic expectations

- 28 records, reference date 2026-10-30.
- INR 300,000.00 programme agreement exposure; INR 340,000.00 potential partnership pipeline.
- 13 open issues, 3 overdue internal tasks, 4 school/sponsor issue records, 3 proposals.
- INC-001 must lead at Critical with CON-001 cited. Other ranks/wording may vary.
- FEAT-001 has no deadline and Routine baseline urgency.
- CAN-002 lacks financial evidence; NOTE-001 and NOTE-002 conflict.
- Completed DONE-001 and cancelled DONE-002 never escalate.

## Recovery and limits

- **Cannot connect:** leave backend/frontend terminals open; check API health and
  restart the failed process. React's error state includes retry. Use the script-free
  README commands if PowerShell blocks scripts.
- **Groq quota/rate limit:** wait and inspect provider limits before another run.
  Do not repeatedly click or switch to paid providers during recording.
- **Rejected output:** show the honest error and retry a shorter question after
  checking readiness. Keep evidence/policy validation enabled.
- **JEV auth/quota error:** stop JEV attempts; use rules. Correct credentials
  privately before a single intentional retry. Preserve successful cache files.
- **Cache save failure:** follow “Do not retry a paid decision”; fix storage first.
- **Backend restart:** jobs are in memory; previous IDs may no longer exist.
- **No accepted real run:** the UI or unit tests do not substitute for a working
  AI demonstration. Historical JSON exports must be labeled as prior results.

Say aloud: “This is a local synthetic demo. Source references are checked, but
founders still review interpretations. Approval stays local. No comparative
JEV accuracy, speed or cost claim is made.”
