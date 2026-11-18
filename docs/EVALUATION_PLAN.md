# Praxis evaluation implementation plan — 2026-11-17

The user authorized implementation in the task specification. No live calls,
JEV requests, commits, deployments, or unrelated edits are authorized here.

## Design

Keep the two-agent sequential CrewAI application. Add a small Python evaluation
package using Pydantic and the standard library, with JSON fixtures under
`data/evaluation/v1`. Reuse real business tools, the application service and its
validators. Offline execution replaces only the crew/provider boundary with
explicitly hand-authored candidate outputs; a separate integration test exercises
the actual CrewAI runtime with a scripted LLM. Neither is a live quality claim.

Gold labels are reviewed literals tied to source IDs, money values, and fixed
dates. Version and hash the suite, datasets, prompts, application source and
recorded candidates. Missing denominators yield null, never perfect scores.

Report raw candidate checks separately from expected accept/reject behavior and
violations on released answers. Include per-case reasons and failure categories.
Citation membership is not semantic entailment. Limited lexical checks of
explicit answer labels are supplemental and must be identified as such.

Live evaluation requires both `--mode live --allow-live` and named live-eligible
cases, defaults to a single case, forces Rules, stops after provider errors, and
uses a killable subprocess per case for a hard evaluation deadline. Existing
provider budgets/cooldowns remain in force. No judge model is needed.

## Implementation and verification

- [x] Establish existing offline-test baseline.
- [x] Add evaluator tests first: malformed outputs, source leakage, arithmetic,
  escalation, action assertions, invalid tool inputs, and report comparison.
- [x] Add versioned inputs/candidates/labels plus deterministic scoring and replay.
- [x] Run and retain the unmodified application's evaluation baseline.
- [x] Fix narrowly demonstrated gaps without relaxing existing policy checks.
- [x] Re-run identical cases, compare compatible reports, and test regressions.
- [x] Add explicit-opt-in, process-bounded live mode and interruption tests.
- [x] Run the complete offline suite, document actual evidence and limitations,
  and provide defensible resume bullets. Leave existing user files untouched.
