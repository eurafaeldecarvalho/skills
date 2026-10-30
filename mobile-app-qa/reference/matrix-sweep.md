# Matrix sweep (pass 4): every screen × theme × locale × font × size

## Emulator on Linux (box or CI)
```bash
export ANDROID_HOME=$HOME/android-sdk JAVA_HOME=$HOME/jdk17
export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
ls -l /dev/kvm                                   # hardware acceleration required
sdkmanager "platform-tools" "emulator" "system-images;android-35;google_apis;x86_64"
avdmanager create avd -n qa35 -k "system-images;android-35;google_apis;x86_64" -d pixel_6
emulator -avd qa35 -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect -no-snapshot-save &
adb wait-for-device; until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ]; do sleep 2; done
adb install -r app-release.apk                   # release build (bundletool if you have an AAB)
for s in window_animation_scale transition_animation_scale animator_duration_scale; do adb shell settings put global $s 0; done
curl -fsSL https://get.maestro.mobile.dev | bash # Maestro (Java 17)
```
Check reservations/load before booting an emulator on a shared machine. A `google_apis` image allows
`adb root` (system locale via `setprop persist.sys.locale` + `stop; start`); per-app locale needs no root.

## Toggles (all restorable — `scripts/adb-env.sh`)
| Axis | Set | Reset |
|---|---|---|
| Theme | `cmd uimode night yes|no` | `cmd uimode night auto` / previous |
| App language | `cmd locale set-app-locales $APP_ID --locales pt-BR` (Android 13+) | `--locales ""` |
| System locale (root image) | `setprop persist.sys.locale pt-BR; stop; start` | previous value |
| Font scale | `settings put system font_scale 1.3` | read first, restore |
| Screen size | `wm size 720x1280; wm density 320` | `wm size reset; wm density reset` |
| Nav mode | `cmd overlay enable com.android.internal.systemui.navbar.gestural` / `.threebutton` | previous |
| 24 h clock | `settings put system time_12_24 24` | previous |
| Network | `cmd connectivity airplane-mode enable` | `disable` |
| Don't keep activities | `settings put global always_finish_activities 1` | `0` |
The app only honours the per-app locale if it reads the Android locale (expo-localization) — if the app
has its own in-app language setting, also drive that (Maestro subflow `set-language`) and sweep both.

## Screens list
`qa/screens.txt`: `name|deeplink` per line (e.g. `expense-new|evenkeel://expense/new`). Screens without
a deep link → a Maestro sweep flow (`templates/maestro/flows/sweep-screens.yaml`) that navigates by
`testID` and calls `takeScreenshot` per screen; the script runs it once per config.
Include states: empty, loaded, error, offline, long data, modal/sheet open, keyboard open.

## Run and check
```bash
APP_ID=com.example.app SCREENS=qa/screens.txt OUT=qa/sweep/$(date +%F-%H%M) scripts/matrix-sweep.sh
python3 scripts/sweep-check.py qa/sweep/<run>     # findings.md, findings.json, contact-*.png
```
Full cross product (4 locales × 2 themes × 3 fonts × 2 sizes = 48 configs) is affordable for ≤30 screens;
otherwise run full on the core screens and pairwise on the rest. Detectors: `blank-screen`,
`us-money` (non-en locale), `raw-key`, `bad-value` (undefined/NaN/null/[object Object]), `small-target`
(<48dp), `stuck-banner` (same banner text on most screens), `untranslated` (English UI words in non-en),
`low-contrast` (heuristic from pixels in text bounds), `clipped-text` (text bounds outside screen).
Then a human/vision review of every contact sheet — dark and each non-English locale at minimum.

## Caveats
Emulator ≠ OEM skin (Moto/Samsung/Xiaomi), ≠ real GPU performance, ≠ real keyboards. The sweep finds
layout/theme/format regressions; the gate still needs a real phone.
