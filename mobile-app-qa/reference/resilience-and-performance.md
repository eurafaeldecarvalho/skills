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
| Session expired | staging: set JWT expiry low (e.g. 60 s) in Auth settings; or wait; sign out other sessions | silent refresh or clean re-login, no data loss, queued writes kept, no refresh loop |
| Removed from space / deleted elsewhere | owner removes member on device A while B is open | B loses access server-side at once, cache cleared, clear message |
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
- Low memory: `adb shell am send-trim-memory <pkg> RUNNING_CRITICAL` (foreground) and `COMPLETE`
  (after Home) → state kept, no crash. Low storage: `adb shell cmd devicestoragemonitor force-low -f`
  (reset: `… reset`) or fill `/sdcard` on the emulator → writes fail gracefully, local DB not corrupted.
- Battery saver (`adb shell settings put global low_power 1`), OEM battery optimization (Xiaomi/Samsung)
  killing background sync — real device.
- Clock/timezone: `settings put global auto_time 0` / `auto_time_zone 0`, then `cmd alarm set-timezone
  America/New_York` and `cmd alarm set-time <epoch-ms>` (or `adb root` + `date` on a non-Play image;
  real phones: Settings). Test while the app is open, DST gap/overlap days, leap day, year boundary.
  Store instants in UTC, civil dates (due dates, birthdays) as dates — never as midnight UTC.
- **Upgrade over an installed build:** install previous production APK/AAB → create data in every
  feature (+ pending offline writes) → `adb install -r` the new release (and later via the Play test
  track) → data intact, migrations ran once, session kept, outbox flushed. Then downgrade is refused
  cleanly. Old client against the migrated backend still works or is force-updated with a message.
- Reinstall and `pm clear`: onboarding works, server data comes back after login, nothing stale.
- TalkBack on/off while the app runs; accessibility services don't crash custom components.

## Performance
Budgets (mid-range device such as a Moto G, release build): cold start to interactive < 2 s (warn > 3 s);
no frame drops on main lists while scrolling (janky frames < 5 %); tap-to-feedback < 100 ms on the main actions; memory
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
