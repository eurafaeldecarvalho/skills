# Convergence loop (pass 7) — run until the findings are zero

The skill is not "one pass and a report". The agent repeats the **whole** pass until a full iteration
finds **nothing** — zero findings of any severity (P0, P1, P2, P3) in every dimension, including the
red-team — and then proves it once more with fresh adversarial inputs.

## One iteration = the FULL pass, never a partial one
```
iteration k:
  2 Audit (code + build)            → findings
  3 Functional E2E (whole suite)    → findings
  3b Live E2E (staging; Play test-track build in the final two iterations) → findings
  4 Matrix sweep (every screen × config) → findings
  5 Harden                          → findings
  6 Critique (fresh eyes; independent sub-agent when possible) → findings
  6b RED-TEAM (new seeds + new corpus slice) → findings
  + regression: every test/flow/probe/detector added in earlier iterations
  → log ledger row k
  if findings == 0: clean streak += 1 else: clean streak = 0; fix (below); k += 1; repeat
```
Re-running only the fixed items is **not** an iteration: fixes break other things (the classic is a
dark-mode fix that breaks light mode, or a locale fix that breaks the parser).

## What counts as a finding
Any failed expectation, crash/ANR, flaky test (a test that failed once in 3 runs **is** a finding), detector
flag not proven false-positive, successful red-team attack, missing `testID`, ⏳ row in `FEATURES.md`,
missing evidence, gate item ❌, copy issue, P3 polish nit. A detector false positive is closed only by
improving the detector (with a test) **and** a human/vision look at the screenshot.

## Fix step (between iterations)
1. Order: P0 → P1 → P2 → P3; security and data before looks.
2. For each finding: reproduce in the exact config → write the **failing** regression test first (unit,
   integration/pgTAP, Maestro, sweep detector or red-team probe) → fix the root cause → test green →
   one commit per finding (`fix(<area>): <finding id> …`).
3. Never fix during a measurement phase; finish the iteration first so counts are honest.

## Exit condition (all true)
- **Two consecutive iterations with zero findings**; the second uses **fresh** randomized/adversarial
  inputs: new monkey seeds, new fuzz corpus slice, new random data, shuffled config/screen order, and a
  different device/emulator profile where available.
- The last two iterations ran on the release candidate; live + red-team ran on the build installed from
  the Play test track.
- Then the **FINAL PASS** ([final-pass.md](final-pass.md)) on the signed release APK installed on clean
  emulators (fresh + update over the previous version) finds zero findings. A FINAL PASS finding is logged
  as `Found in: FINAL`, fixed like any other, and the loop restarts (two clean iterations, then FINAL again).
- The release gate in SKILL.md is fully ✅.

## Iteration ledger (in the report; one row per iteration)
| Iter | Build | Seeds | P0 | P1 | P2 | P3 | Total | Fixed since last | New | Regressions | Blocked | Clean streak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
Plus a findings table where every ID keeps its history (found in iter, fixed in commit, verified in iter).

## Anti-cheating rules
- Never lower a severity to make the count go down; re-classification needs a written reason and the
  original severity stays visible in the ledger.
- Never delete, skip, `.only`, quarantine or loosen a test/flow/probe/detector to get green; assertions
  only get stricter. Flaky ≠ skip: fix the flake.
- Never shrink the matrix, the locale list, the device list or the red-team corpus between iterations.
- No "won't fix" / "accepted" without the **owner's explicit written approval**; accepted items are
  listed separately and the report says "not zero" — they are not counted as fixed.
- Findings the agent cannot fix itself (needs owner decision, paid service, console access, a real
  device, another team's backend) are **Blocked**: listed with what's needed, never zeroed. While any
  finding is Blocked the loop cannot declare "zero".
- Never claim a clean iteration that skipped a phase; a skipped phase = iteration invalid. An iteration
  paused because the machine slot ended resumes in the next slot ([shared-machine.md](shared-machine.md));
  it counts only once every phase ran.
- Never test against real users or production data to "get more coverage".

## Safety cap / escalation
- Weighted score = 8·P0 + 4·P1 + 2·P2 + 1·P3.
- **Stop and escalate** to the owner (report + blockers + hypotheses) when any of these happens:
  3 consecutive iterations without a decrease in weighted score; the same finding regresses twice;
  10 iterations total; a P0 security finding in production data; the remaining findings are all Blocked;
  the environment constraints (time window, budget, no emulator) prevent a phase.
- Escalation is a report, not a shortcut: the gate stays FAIL.
