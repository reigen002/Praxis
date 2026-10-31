# Your test drive

Open **http://127.0.0.1:8000**. Use a maximized desktop browser at 100% zoom.
The API serves the built React frontend, so only one server is required.

If it is stopped, open PowerShell and leave this command running:

```powershell
cd D:\Projects\Praxis
uv run --frozen --cache-dir .cache/uv python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8000
```

## Repeatable walkthrough — no new model calls

1. **Overview.** Keep **YFS founder demo** selected. This is fictional school
   programme data with reference date **30 October 2026**. Check the cards:
   **₹300,000.00** programme agreement exposure, **₹340,000.00** potential
   partnership pipeline, **13** open issues and **3** overdue tasks. Click the
   information icon to inspect each metric's definition and eligible sources.
2. **Morning briefing.** Below the question box, click **Open saved briefings**,
   then **Open morning briefing**. The summary must say **Saved real run**, with
   the original execution duration. These are accepted outputs from real CrewAI
   executions, not generated placeholders. The prepared morning run took about
   **78.6 seconds** originally; reopening it makes no new model call.
3. **Evidence and priorities.** Inspect the leading **Learner portal access
   broken** priority. Open **INC-001**, then its linked **CON-001** agreement.
   Open **NOTE-001** and **NOTE-002** through linked evidence to see the conflicting
   recovery reports. Expand **Assumptions & missing context**. Close the drawer
   with its close button or Escape. Source references are validated; interpretations
   still require human review.
4. **Search and missing data.** Open **Business updates**. Search **FEAT-001**:
   the certificate redesign has no recorded deadline. Search **CAN-002** to see
   missing financial information. Clear the search and try status/category filters.
   Completed or cancelled work appears in the records but is not escalated.
5. **Human review.** Open **Follow-up review**. Read the draft and its evidence.
   Try **Copy draft**, then **Approve locally**, then **Reject**. Approval status
   changes in this browser only. No message is sent and no CRM is updated.
6. **Execution and export.** Open **Execution activity**. Show the Analyst's
   actual retrieval tool and the Chief of Staff's validated completion. The
   timestamps belong to the original saved execution. Return to **Overview** and
   click **Export briefing**. The JSON download retains the original run ID and events.
7. **Decision explanation.** Open saved briefings again and choose **Open
   decision explanation**. It answers: “Why is the cohort access issue more urgent
   than the certificate preview redesign?” Inspect the answer, priorities, sources
   and limitations. This is a separate real execution, originally about **105.3
   seconds**, with its own activity. Opening it resets local draft reviews.
8. **Optional JEV.** Switch the dataset to **Startup demo**. Open
   **Decision lab**, leave **INC-001** selected, and click **View saved live
   decision**. Expect **Engineering**, **Critical**, expected urgency **2.97 / 3**,
   and relationship risk estimate **86.0%**. Compare with the rules score **3 / 3**.
   Show the distribution and provider provenance. This is a genuine earlier JEV
   result for a separate startup example, not for the school dataset. The saved
   button now uses a read-only cache endpoint and cannot start a new evaluation.

To repeat: switch back to YFS, refresh, and reopen the saved morning briefing.
The saved results survive refresh and server restarts. Local approval decisions
reset, so you can demonstrate approval again. Dataset changes clear the current
view; they do not delete the prepared results.

## Try a fresh live run separately

Keep **YFS founder demo** and **Rules signals** selected. Use this exact prompt:

> Prepare my founder briefing for today. What are the three most important issues, and why?

Click **Prepare my briefing** once. This always starts real CrewAI execution;
it does not silently substitute a saved result. You can inspect business records
while it runs. A success shows **Live run complete** and automatically saves the
accepted result for the next viewing. A changed question starts a fresh run too.

Live Groq latency and quota remain variable. If it reports a cooldown, follow the
displayed wait instead of repeatedly clicking. A provider/validation error is not
a completed briefing. Reopen a prepared saved run explicitly to continue practicing.
Avoid **Evaluate with JEV · uses one request** during rehearsal: that is a new
evaluation, distinct from **View saved live decision**.

## What to say in the video

“These are synthetic operating records inspired by Young Founders School's
programmes. Two real CrewAI agents produced the briefing. For this walkthrough
I'm reopening their saved execution, including its original activity, so the
recording doesn't depend on fresh API latency. The live-run control is separate.
Python calculates metrics and enforces mandatory escalation; model judgments and
drafts remain subject to founder review.”

Use [LOOM_DEMO.md](LOOM_DEMO.md) for the timed 3–5-minute script and the shorter
90-second option. Do not narrate saved runs as new or instantaneous inference.
