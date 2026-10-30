# Feedback loop (dimension 11)

Every report from a tester is data. The loop: **log → reproduce → fix → regression check → re-verify on
the failing device → close.**

1. **Log** with [templates/bug-template.md](../templates/bug-template.md), in one place (e.g. `qa/bugs.md` or issues). One bug per entry;
   ask for device, input and what they expected if missing.
2. **Reproduce** on the same device class/input (emulator first, then real device). If it doesn't
   reproduce, write what you tried and keep it open as "needs info" rather than closing it.
3. **Find the class, not just the instance.** The fryer-over-dough prompt bug means *every* pair of close
   prompts is suspect; the tap-only countdown means *every* overlay needs an auto-exit. Sweep for siblings.
4. **Fix** the cause at the narrowest correct level; one bug per commit with the bug ID in the message.
5. **Regression check**, the strongest available:
   - Lune unit test for pure logic;
   - a scripted Studio check (via MCP or a test runner) for DataModel invariants (prompt spacing,
     safe insets, text sizes, overlay timeouts);
   - otherwise a named manual step added to `qa/manual-checks.md` ([template](../templates/manual-checks.md)),
     re-run in every FINAL PASS until a script covers it.
   Write the check first and see it fail before the fix (convergence-loop.md).
6. **Re-verify on the device type that failed** (real hardware if that's where it was reported), then
   mark verified. Ask the reporter to confirm when possible.
7. **Update the catalog**: add new bug classes to anti-patterns.md so the next pass checks them.

Triage cadence: after each playtest session, re-score the affected dimensions, start a new iteration of the
convergence loop (the whole pass, not only the fixed items) and re-run the release gate. Tester bugs on devices
or player counts you could not reproduce stay open as **Blocked** with the missing resource named.
