# Device clouds and CI emulators (where to run the emulator and real-device passes)

Which services actually work for the emulator passes (functional E2E, matrix sweep, FINAL PASS) and for
real-device reach when the local machine can't run a usable emulator. **Ranked by what was really tested**
(2026-10-30, Expo/RN release APK, Maestro flows by `testID`), not by marketing pages. Free tiers change:
re-check quotas before relying on them, and anything that needs a card or a paid plan needs the owner's
approval.

| # | Service | Verdict | Free tier | Best for |
|---|---------|---------|-----------|----------|
| 1 | **GitHub Actions + `reactivecircus/android-emulator-runner`** (ubuntu-latest) | ✅ works — default choice | 2,000 min/month on private repos (Free plan), unlimited on public | Maestro suite, smoke/sweep, font/night screenshots, logcat scan, API 30 + 34 on every build |
| 2 | **Firebase Test Lab** (Spark plan, no card) | ✅ works — temporary | 10 virtual + 5 physical device runs/day | Robo crawl on devices you don't own, screenshots + video |
| 3 | **Google Play internal testing + pre-launch report** | ⚠️ partly confirmed | free with a verified Play developer account | store-installed build on real phones; pre-launch crawl (**needs confirmation** on internal) |
| 4 | **Samsung Remote Test Lab** | ⚠️ manual only | 20 credits (30-min session = 2 credits) | real Galaxy devices (incl. Brazil), Android 15-17, from a normal desktop browser |
| — | TestingBot, AWS Device Farm, Android Device Streaming | ❌ not recommended | — | see below |
| — | BrowserStack, Sauce Labs, Kobiton, Genymotion Cloud | trials only | time-limited | one-off checks with the owner's OK |

**Local machine without nested KVM** (a VM/box where `emulator -accel-check` fails): the emulator only
runs with `-accel off`, cold boot ~15 min and every step crawls — too slow for a matrix sweep or a FINAL
PASS. Prefer GitHub Actions (1) and keep the box for builds, detectors and report work.

## 1. GitHub Actions emulator (recommended)
Template: [`templates/ci/android-emulator-maestro.yml`](../templates/ci/android-emulator-maestro.yml)
(self-contained: writes its in-emulator script, `workflow_dispatch` inputs for package, APK tag, API
levels, target, profile, Maestro dir and gating flows; uploads `out/` as evidence).

**Measured (2 vCPU / 8 GB runner, swiftshader GPU):** `accel-check` → *KVM is installed and usable* (the
udev rule step makes `/dev/kvm` usable for the runner user); cold AVD boot **35-58 s**, launch-to-ready
21-47 s, whole job **~10-13 min per API level** including install, Maestro discovery/smoke/sweep, the full
suite (informational), font 1.3 + night-mode screenshots and a logcat crash/ANR scan. Matrix jobs run in
parallel; each bills its own minutes.

**Always run two API levels:** `api-levels='[30, 34]'` — API 30 boots with **3-button navigation**, API 34
with **gesture navigation**, so one dispatch covers both nav modes of the insets gate item.

```bash
# APK as a release asset (never committed to git); x86_64 ABI must be inside (universal or x86_64 split)
gh release create apk-vc7 qa/final/app-release.apk --prerelease --title "QA apk vc7"
gh workflow run android-emulator-maestro.yml -f app-id=com.example.app -f apk-tag=apk-vc7 \
  -f api-levels='[30, 34]' -f gating-flows='.maestro/flows/smoke.yaml .maestro/flows/sweep-screens.yaml'
gh run watch && gh run download <run-id> -D qa/ci/<run-id>     # screens/, ui/, maestro/ junit, logcat*.txt, steps.txt
```

**Token / permissions:** pushing a workflow file needs the classic `workflow` scope or, for a fine-grained
PAT, **Contents: read/write, Actions: read/write, Workflows: read/write** on that repo. `gh run view`
may print a 403 on check-run *annotations* with a fine-grained PAT — harmless, the run and logs are fine.
The job itself needs no secrets; if flows need credentials, use repo secrets → env → `maestro -e KEY=$KEY`.
Never commit tokens, keystores or APKs.

**Lessons (each one cost a failed run):**
- **Give the emulator 3 GB RAM** (`ram-size: 3072M`). Fresh AVDs on 2 vCPU show *"Pixel Launcher isn't
  responding"* over the app and every `testID` selector fails.
- **Hide system error dialogs** (`settings put global hide_error_dialogs 1`; crashes still land in logcat),
  **settle 20 s** after `sys.boot_completed`, and **auto-dismiss "isn't responding"/"keeps stopping"**
  dialogs (tap *Wait*/*Close* from a uiautomator dump) before every step and screenshot. Log each
  dismissal (`infra-dialogs.txt`) so infra noise is not mistaken for an app ANR.
- **`scrollUntilVisible`** for anything below the fold (pixel_6 profile, 1080×2400 @ 420 dpi); a flow that
  passes on your phone can fail here only because the target is off-screen.
- **Emulator locale is en-US**: the system share sheet says *"Sharing"*, not *"Compartilhar"*; match system
  UI with a locale-tolerant regex (`"(Sharing|Compartilhar).*"`) or set the locale explicitly.
- **AVD cache is not saved when the job fails** (`actions/cache` saves only on success): the first green
  run per API level/target/profile warms it; until then every run pays the cold AVD creation.
- `emulator -accel-check` only exists after the runner action installs the emulator → run it in-script.
- The runner's `script:` executes line by line → keep the logic in one bash file (the template writes it).
- A flow that fails **only on API 30** with a bottom CTA is usually the app ignoring safe-area insets under
  the 3-button bar: a real app bug, not infra.

**Measured example (Plano de Corte, Expo/RN, 2026-10-30):** API 30 + 34 runs found a **P0 inset bug** —
the bottom primary CTA sat under the 3-button navigation bar on API 30, so the main flow could not be
completed there. It was invisible in the web build and on the developer's gesture-nav phone; only the
3-button emulator run exposed it. Discovery + smoke + sweep + font/night screenshots + logcat ran in
~10-13 min per API level.

## 2. Firebase Test Lab (Spark, no card)
- Works on the free Spark plan without a billing account: **10 virtual + 5 physical device runs/day**.
- Measured: **Robo test on Pixel 5 (virtual), API 30** — passed, 62 actions, 17 screens, ~5 min;
  screenshots, video and logcat in the Firebase console (Test Lab → test matrix).
- Upload the release APK (console or `gcloud firebase test android run --type robo --app app.apk
  --device model=<id>,version=30`; ids from `gcloud firebase test android models list`). Give Robo a test login (robo directives/script) or it stops at sign-in.
- **Temporary:** Google announced the Test Lab shutdown on **2027-09-30**. Use it for extra device reach,
  never as the only CI.

## 3. Google Play internal testing + pre-launch report
- Requires a **verified Play developer account**. Upload the AAB to the **internal testing** track: no
  review, available to listed testers immediately → install from Play on a real phone (store-installed
  smoke test, Play signing and splits included).
- **Pre-launch report:** did **not** appear right after an internal-track upload; the console suggests
  closed testing triggers it. Status: **needs confirmation** — check *Testing → Pre-launch report* after
  a closed-track upload before counting it as evidence.

## 4. Samsung Remote Test Lab (real Galaxy devices)
- Free developer account (Google sign-in + Samsung 2FA on the owner's phone — the owner must be present);
  **20 free credits**, a 30-min session = 2 credits. Many real Galaxy models, including devices located in
  **Brazil (Manaus)**, Android 15-17.
- APK upload/install through the web UI works (~40 s for a 63 MB APK).
- **Limitation:** the live screen stayed **black in a headless/box Chrome** (WebRTC video stream). Use it
  from a normal desktop browser for manual One UI checks (Samsung keyboard decimal pad, One UI dark mode,
  font size/style); **not usable for automated agent QA yet**.

## Not recommended / trials only
- **TestingBot:** free trial not available in Brazil; the account showed minutes paused (the "10 live
  sessions/month" exists only on paper).
- **AWS Device Farm:** needs a credit card even for the free minutes — owner's approval required.
- **Android Device Streaming** (Firebase/Android Studio): needs the Android Studio GUI, ~30 min/month free;
  not tested.
- **BrowserStack, Sauce Labs, Kobiton, Genymotion Cloud:** time-limited trials only; fine for a one-off
  device check with the owner's OK, not for the loop.

## How this maps to the pass
- Passes 3, 4, 7b on a machine without KVM → GitHub Actions template, API 30 + 34, evidence downloaded
  into `qa/ci/<run-id>/` and cited by run id in findings.
- Extra device reach (other OEMs/sizes) → Firebase Test Lab Robo (while it lasts) + Samsung RTL by hand.
- Gate "store-installed build on a real phone" → Play internal track; pre-launch report from a closed track.
- None of these replaces the gate's **real low/mid phone + real testers**; say which evidence came from
  CI emulators, which from cloud devices and which from hardware.
