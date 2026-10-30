# FINAL PASS (mandatory): install the real release APK and run the real app

The convergence loop proves the code; the FINAL PASS proves **the artifact users will install**. It runs
after the loop reports two clean iterations and before the gate. It is not a smoke test: it repeats the
whole pass on the signed release artifact installed with `adb install` on clean emulators, then (when
available) on a real phone from the Play closed-test track.
**Any finding in the FINAL PASS restarts the convergence loop** (fix → full iteration → two clean
iterations → FINAL PASS again). The FINAL PASS itself must come out with zero findings.

## 1. Build the exact release artifact
Same commit, same `versionCode`, same signing as the upload to Play — never a debug or dev-client build.
```bash
# Local (heavy — reserve the box first, see shared-machine.md) or EAS (`eas build -p android --profile production`)
cd android && nice -n 10 ./gradlew bundleRelease --max-workers=2 -Dorg.gradle.jvmargs=-Xmx3g && ./gradlew --stop          # → app/build/outputs/bundle/release/app-release.aab
# AAB → installable universal APK, signed with the upload key (keystore values from env/secret store, never printed)
bundletool build-apks --bundle app-release.aab --output qa/final/app.apks --mode=universal \
  --ks "$UPLOAD_KS" --ks-key-alias "$UPLOAD_KS_ALIAS" \
  --ks-pass "pass:$UPLOAD_KS_PASS" --key-pass "pass:$UPLOAD_KEY_PASS"
unzip -p qa/final/app.apks universal.apk > qa/final/app-release.apk
# or a release APK directly: ./gradlew assembleRelease
apksigner verify --print-certs qa/final/app-release.apk | grep -E 'Signer #1 certificate (DN|SHA-256)'  # release/upload cert, not debug
aapt2 dump badging qa/final/app-release.apk | grep -E "package:|targetSdk|application-label"           # versionCode/targetSdk as expected
```
Also keep the **previous released version's APK** (same signing key) for the update test — download it
from the store test track/EAS artifacts or rebuild that tag. Record SHA-256 of both APKs in the report.

## 2. Clean emulators on a headless Linux box
Two profiles minimum: **mid-range** (1080×2400, ~420 dpi, Android 14 *and* 15/16) and **small screen**
(720×1280-class, ~320 dpi). Prefer `google_apis_playstore` images (Play Services for FCM, Play Store for
the track install); `google_apis` when you need `adb root`.
```bash
export ANDROID_HOME=$HOME/android-sdk JAVA_HOME=$HOME/jdk17
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
ls -l /dev/kvm                                    # KVM required; without it the run is too slow to be meaningful
yes | sdkmanager --licenses >/dev/null
sdkmanager "platform-tools" "emulator" "build-tools;35.0.0" \
  "system-images;android-34;google_apis_playstore;x86_64" \
  "system-images;android-35;google_apis_playstore;x86_64"
# mid-range Android 14 + 15, small-screen Android 14 (all start from a wiped userdata)
echo no | avdmanager create avd -f -n final34 -k "system-images;android-34;google_apis_playstore;x86_64" -d pixel_6
echo no | avdmanager create avd -f -n final35 -k "system-images;android-35;google_apis_playstore;x86_64" -d pixel_6
echo no | avdmanager create avd -f -n final34s -k "system-images;android-34;google_apis_playstore;x86_64" -d "Nexus 4"
# force the mid-range geometry (1080x2400 @ 420) on the pixel_6 AVDs
for a in final34 final35; do printf 'hw.lcd.width=1080\nhw.lcd.height=2400\nhw.lcd.density=420\nhw.ramSize=4096\n' >> ~/.android/avd/$a.avd/config.ini; done
nice -n 10 emulator -avd final34 -memory 4096 -cores 4 -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect -wipe-data -no-snapshot -port 5554 &
export ANDROID_SERIAL=emulator-5554
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ]; do sleep 2; done
adb shell input keyevent 82                        # unlock
adb shell wm size; adb shell wm density; adb shell getprop ro.build.version.release
```
`scripts/final-pass.sh` wraps these (`setup`, `boot <avd> [port]`, `install`, `update-prev` + `update`, `evidence`,
`record`, `logscan`, `perf`, `stop`).
On a shared machine: book a slot and hold the lock first ([shared-machine.md](shared-machine.md));
`final-pass.sh` refuses to `setup`/`boot` without it, caps the emulator at `-memory 4096 -cores 4` under
`nice`/`ionice`, prefixes AVDs with your project, and `stop` kills only your emulator. One emulator per agent,
so run the profiles one after another; if the slot ends, pause and resume in the next one.

## 3. Install — both ways
| Case | Commands | Oracle |
|---|---|---|
| **Fresh install** | `adb uninstall <pkg>` (ignore error) → `adb install qa/final/app-release.apk` | first launch shows onboarding/sign-in; no crash; permissions asked in context |
| **Update over previous version** | wipe → `adb install prev.apk` → sign in, create real data (expenses, events, pending offline write) → `adb install -r qa/final/app-release.apk` | session kept, all data intact, migrations ran once, offline outbox flushed, no re-onboarding, push token still registered |
| Downgrade guard | `adb install -r -d prev.apk` over the new one must be refused unless intentionally supported | no silent data loss |
| Signature continuity | update succeeds without `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | same key as store |

## 4. Run the real app — everything, on the installed artifact
Per emulator profile (mid-range A14, mid-range A15/16, small screen), both nav modes:
1. **Full feature walkthrough** by hand/agent: every row of `FEATURES.md`, as a first-time user, then as
   a returning user. Screen-record it.
2. **Live backend flows** (staging/QA project per [live-e2e.md](live-e2e.md)): real sign-up with a tagged
   address, email arrives and the link opens the app, two-account invite/sharing, money and dates, push
   (fg/bg/killed — Play-services image), account deletion, cleanup verified.
3. **Maestro suite** in full: `maestro test .maestro/ --format junit --output qa/final/maestro.xml`.
4. **Matrix sweep** (`scripts/matrix-sweep.sh` + `sweep-check.py`) on this install — zero detector flags.
4b. **Launch/splash pass** on this install: `scripts/splash-capture.sh` (cold + warm + hot × light + dark ×
   small / 1080×2400 / tablet) → `sweep-check.py --splash --logo` clean, strips reviewed, launcher icon
   (normal, themed, round) checked → [launch-and-visual-precision.md](launch-and-visual-precision.md).
5. **Red-team quick pass**: monkey with 3 fresh seeds (`red-team-chaos.sh monkey 5000 <s1> <s2> <s3>`),
   kill mid-write, airplane mid-write, back spam, revoke permissions, clear data; `rls-probe.sh` on the
   core tables with the stranger account; APK secret grep (S12) on *this* APK.
6. **Logs and performance** during all of the above:
   - `adb logcat -c` before; `adb logcat -d '*:E' > qa/final/<avd>/logcat-errors.txt` after; plus the
     crash buffer `adb logcat -d -b crash`.
   - Findings: any `FATAL EXCEPTION`, `ANR in <pkg>`, `ReactNativeJS` errors, `Unhandled promise`,
     `SQLiteException`, `NetworkOnMainThread`, `StrictMode` from the app, repeated warnings from the app's
     PID (`adb shell pidof <pkg>` → `adb logcat -d --pid=<pid>`), tokens/emails/PII in any line.
   - `adb shell dumpsys gfxinfo <pkg> reset` before a scroll-heavy flow, `dumpsys gfxinfo <pkg>` after:
     janky frames % and 90th/99th percentile frame time in the report (> 10 % janky on main lists = finding).
   - `adb shell am start -W -n <pkg>/.MainActivity` cold start (`TotalTime`), `dumpsys meminfo <pkg>`.
   - `adb shell dumpsys activity exit-info <pkg>` (Android 11+) after the session: no unexpected
     `CRASH`, `ANR`, `LOW_MEMORY` exits.
7. **Evidence**: screenshots per screen (`adb exec-out screencap -p > shot.png`) and video
   (`adb shell screenrecord --bit-rate 4000000 --time-limit 180 /sdcard/final-<n>.mp4`, then `adb pull`;
   chain several ≤180 s clips for long flows). Stored under `qa/final/<avd>/`, referenced from the report.

## 5. Real device from the Play closed-test track (preferred, when available)
Upload the same AAB to the closed/internal track → install **from the Play Store** on a real mid-range
phone signed into a tester account (and, if possible, update over the previous track version) → repeat
steps 4.1–4.3 and 4.6 there. This is the only way to catch Play-signing, App Bundle splits, Play
Integrity, real OEM skins and real push. If no device is available, the FINAL PASS is still required on
emulators, and the report lists "real-device track install" as **Blocked** (not zero).

## 6. Exit
FINAL PASS = clean only if: both installs succeed; every step on every profile ran; zero findings of any
severity; logcat errors from the app = 0 (or each one explained and owner-approved); evidence attached.
Otherwise every finding goes to the ledger with `Found in: FINAL` and the convergence loop restarts.
