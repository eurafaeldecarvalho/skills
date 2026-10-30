# Convergence loop — repeat the pass until it finds nothing new

One pass + a report is not done. Repeat the **whole** pass until a full iteration finds no P0–P2 finding,
then prove it once more with fresh adversarial inputs. (Lighter than a "zero of everything" loop on purpose:
P3 polish is tracked but does not keep the loop alive; Roblox QA on a shared box is expensive.)

## One iteration = the full pass, never a partial one
```
iteration k  (inside a booked machine slot for the Studio parts — shared-box.md):
  1 Audit        verify.sh (FLAKE=3) + FEATURES.md rows   → findings
  2 Critique     play the real build (MCP play / Clients and Servers / operator script) → findings
  3 Harden       fake-server scenarios + join/leave/data      → findings
  3b Red-team    red-team.md rows with NEW seeds              → findings
  4 Adapt        ui-audit on every reachable screen + viewport/locale matrix → findings
  + regression   every test, check, manual check and detector added in earlier iterations
  → ledger row k (report template)
  if no P0/P1/P2: clean streak += 1   else: clean streak = 0, fix (below), k += 1
exit when clean streak = 2 (the second clean iteration with fresh seeds), then FINAL PASS (final-pass.md)
```
Re-running only the fixed items is not an iteration: a fix for one viewport breaks another, a rate limit
breaks the legitimate double tap.

## What counts as a finding
A failed expectation; an Output/F9 error or warning not on the documented allow-list; a flaky test (red once in
3 runs **is** a finding); a detector hit not proven false; a successful red-team attack; a ⏳ row in FEATURES.md;
a gate item ❌; a claim without its evidence source. A detector false positive is closed only by improving the
detector (with a test) **and** a look at the real screen.

## Fix step (between iterations)
1. Write the failing regression check first (Lune test, fake-server scenario, ui-audit rule, or a named line in
   `qa/manual-checks.md`), see it red.
2. Fix the root cause; one finding per commit, ID in the message. Sweep for siblings ("find the class").
3. See the check green ×3, then continue to the next iteration (which re-runs everything).

## Rules (no gaming the loop)
- Never lower a severity to exit; the ledger keeps "original → current" and a reason for any change.
- Never skip, delete, loosen or mark expected-fail a test or detector to get green; never shrink the matrix
  (viewports, locales, inputs, player counts, red-team rows) between iterations.
- Items you can't verify (no slot, no device, no people) are **Blocked** with the reason; they never count as zero.
- Owner-accepted risk is written in the report by the owner, with the finding ID; the agent never accepts its own P1.

## Safety cap (escalate, don't spin)
Weighted score = 8·P0 + 4·P1 + 2·P2 + 1·P3. Stop and report to the owner when: the score doesn't fall for 3
iterations; the same regression comes back twice; or 6 iterations ran. Include the ledger and the top blockers.
