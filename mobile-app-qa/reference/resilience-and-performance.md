# Resilience & lifecycle (dimension 8) and performance (dimension 9)

## Network
| Case | How | Expected |
|---|---|---|
| Offline at launch | `adb shell cmd connectivity airplane-mode enable` then launch | cached data, clear offline UI, no spinner forever |
| Lose network mid-write | enable airplane mode right before submit | queued or clear error; no duplicate on reconnect |
| Recover | disable airplane mode | banner clears **by itself** within the retry interval; queue flushes once |
| Slow / lossy | emulator `adb emu network speed gsm` / `adb emu network delay umts` | timeouts handled, skeletons, cancelable |
| Captive portal / no internet on Wi-Fi | Wi-Fi without internet | `isInternetReachable` false or `null` (= **unknown**, not offline) |
| Server error 500/timeout | test backend toggle, proxy, or mock | error ≠ offline; retry with backoff; message says what to do |
| Session expired | wait >1 h / revoke token | silent refresh or clean re-login, no data loss |
Every degraded-state banner: entry condition, exit condition re-checked (timer + foreground + network
event), manual retry/dismiss, never covers primary actions, localized.

## Lifecycle
- **Don't keep activities** (`adb shell settings put global always_finish_activities 1`) + background/
  foreground on every screen with a form → state restored or safely discarded with a warning.
- Process death: `adb shell am kill <pkg>` while in background → reopen → correct screen/state, no crash.
- Cold start from notification and deep link while logged out / logged in.
- Rotate (if allowed), split-screen, change theme/language/font **while the app is open** → re-render.
- Permissions: `adb shell pm grant|revoke <pkg> android.permission.POST_NOTIFICATIONS|CAMERA|READ_MEDIA_IMAGES`;
  first ask, denied, "don't ask again", revoked from settings while running → app explains and recovers.
- Low storage, low battery saver, OEM battery optimization (Xiaomi/Samsung) killing background sync.
- Clock changes (set time manually, timezone change) for schedule features.
- Upgrade from previous release with existing data (`adb install -r`).

## Performance
Budgets (mid-range device such as a Moto G, release build): cold start to interactive < 2 s (warn > 3 s);
no frame drops on main lists while scrolling (janky frames < 5 %); input latency imperceptible; memory
stable across 10× navigate-back loops; APK/AAB size tracked.
```bash
adb shell am start -W -S -n <pkg>/.MainActivity         # TotalTime (cold start)
adb shell dumpsys gfxinfo <pkg> reset; # scroll the list…
adb shell dumpsys gfxinfo <pkg> | grep -E "Janky frames|90th|95th|99th"
adb shell dumpsys meminfo <pkg> | grep -E "TOTAL|Java Heap|Native Heap"
adb logcat -b crash -d ; adb logcat -d | grep -E "ANR|FATAL|ReactNativeJS"
```
Emulator numbers are not representative (software GPU under KVM) — performance scores come from real
hardware; the emulator only catches regressions. RN specifics: FlashList/FlatList with stable keys and
`getItemLayout` where possible, no heavy work in render, memoize list rows, images sized, Hermes on,
avoid re-render storms from context. Flashlight / Android Studio profiler / Perfetto for deeper work.
Stability: zero crashes in logcat during the whole sweep and E2E suite; Android vitals thresholds
(user-perceived crash rate < 1.09 %, ANR < 0.47 %) after release.
