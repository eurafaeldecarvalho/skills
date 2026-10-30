# Feedback loop (dimension 11, pass 9)

1. Every tester report → bug using [../templates/report-template.md](../templates/report-template.md):
   device model, Android version, OEM skin, theme, language/region, font/display size, nav mode, app
   version/build, steps, expected, actual, screenshot/video, frequency.
2. **Reproduce in the same config** first (emulator with the same toggles via `scripts/adb-env.sh`, or the
   same device class). If it doesn't reproduce: write what was tried and ask the reporter for a screen
   recording or a `adb bugreport`/logcat (only with consent; scrub personal data).
3. Classify P0–P3, find the root cause (not the symptom), fix one thing, add the regression test at the
   cheapest layer that would have caught it (unit → component → Maestro → sweep detector), re-verify in
   the failing config **and** the default config.
4. If it's a new class of bug, add it to [anti-patterns.md](anti-patterns.md) and, when possible, a
   detector to `scripts/sweep-check.py`.
5. Close the loop with the tester: what was fixed, in which build, ask to re-test.
6. After release: Play Console vitals, crash reporter, reviews (in every language) triaged weekly.
