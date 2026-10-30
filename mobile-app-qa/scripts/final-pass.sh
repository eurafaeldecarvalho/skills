#!/usr/bin/env bash
# final-pass.sh — FINAL PASS helpers: clean emulators, install the release APK, collect evidence.
# Usage: final-pass.sh setup | boot <avd> [port] | install <apk> | update-prev <prev.apk> | update <new.apk>
#        | evidence <name> | record <name> [seconds] | logscan | perf | stop
# Env: PKG (app package, required for install/update/logscan/perf), OUT (default qa/final/<serial>),
#      BOX_PROJECT (required: your reservation, see box-reserve.sh), AVD_PREFIX (default: slug of BOX_PROJECT),
#      EMU_MEM (MB, default/max 4096), EMU_CORES (default/max 4). BOX_FORCE=1 or --force skips the reservation check.
# Shared machine: setup only ADDS SDK packages; boot refuses without a valid lock; stop kills only OUR emulator.
# Never prints signing secrets; does not touch production data. Heavy: respect machine reservations.
set -euo pipefail
cmd=${1:-}; shift || true
HERE="$(cd "$(dirname "$0")" && pwd)"
FORCE=${BOX_FORCE:-0}; args=(); for a in "$@"; do [ "$a" = --force ] && FORCE=1 || args+=("$a"); done; set -- "${args[@]+"${args[@]}"}"
PFX=${AVD_PREFIX:-$(echo "${BOX_PROJECT:-qa}" | tr 'A-Z ' 'a-z-' | tr -cd 'a-z0-9-')}
EMU_MEM=$(( ${EMU_MEM:-4096} > 4096 ? 4096 : ${EMU_MEM:-4096} )); EMU_CORES=$(( ${EMU_CORES:-4} > 4 ? 4 : ${EMU_CORES:-4} ))
reserved(){ [ "$FORCE" = 1 ] && { echo "WARN: --force, reservation not checked"; return 0; }
  [ -n "${BOX_PROJECT:-}" ] || { echo "set BOX_PROJECT and reserve a slot first (box-reserve.sh)"; exit 4; }
  "$HERE/box-reserve.sh" check -p "$BOX_PROJECT" -r "$1" || { echo "refusing: no valid '$1' reservation for $BOX_PROJECT (box-reserve.sh status / reserve / acquire)"; exit 4; }; }
SERIAL=${ANDROID_SERIAL:-emulator-5554}; export ANDROID_SERIAL=$SERIAL
OUT=${OUT:-qa/final/$SERIAL}; mkdir -p "$OUT"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$OUT/final.log"; }
need_pkg(){ [ -n "${PKG:-}" ] || { echo "set PKG=<package>"; exit 2; }; }
case "$cmd" in
  setup)
    reserved emulator
    # add-only on the shared SDK: never --uninstall, never replace cmdline-tools/platform-tools another agent uses
    [ -e /dev/kvm ] || echo "WARN: /dev/kvm missing — emulator will be unusably slow"
    yes | sdkmanager --licenses >/dev/null || true
    sdkmanager "platform-tools" "emulator" "build-tools;35.0.0" \
      "system-images;android-34;google_apis_playstore;x86_64" "system-images;android-35;google_apis_playstore;x86_64"
    for spec in "final34:34:pixel_6" "final35:35:pixel_6" "final34s:34:Nexus 4"; do
      IFS=: read -r n api dev <<<"$spec"; n="$PFX-$n"
      [ -d "$HOME/.android/avd/$n.avd" ] && { echo "AVD $n exists (ours) — reusing"; continue; }
      echo no | avdmanager create avd -f -n "$n" -k "system-images;android-$api;google_apis_playstore;x86_64" -d "$dev"
      if [ "$dev" = pixel_6 ]; then
        printf 'hw.lcd.width=1080\nhw.lcd.height=2400\nhw.lcd.density=420\nhw.ramSize=4096\n' >> "$HOME/.android/avd/$n.avd/config.ini"
      fi
    done ;;
  boot)
    reserved emulator
    avd=${1:?avd}; port=${2:-5554}; export ANDROID_SERIAL=emulator-$port
    case "$avd" in "$PFX"-*) ;; *) avd="$PFX-$avd";; esac
    adb devices | grep -q "^emulator-$port" && { echo "port $port already in use (another agent?) — pick another port"; exit 4; }
    nohup nice -n 10 ionice -c2 -n7 emulator -avd "$avd" -port "$port" -memory "$EMU_MEM" -cores "$EMU_CORES" \
      -no-window -no-audio -no-boot-anim -gpu swiftshader_indirect -wipe-data -no-snapshot >"qa/final/emulator-$avd.log" 2>&1 &
    echo "$!" > "qa/final/emulator-$port.pid"
    adb -s "emulator-$port" wait-for-device
    until [ "$(adb -s emulator-$port shell getprop sys.boot_completed | tr -d '\r')" = 1 ]; do sleep 2; done
    adb -s "emulator-$port" shell input keyevent 82
    echo "booted emulator-$port: $(adb -s emulator-$port shell wm size | tr -d '\r') $(adb -s emulator-$port shell wm density | tr -d '\r') Android $(adb -s emulator-$port shell getprop ro.build.version.release | tr -d '\r')" ;;
  install)
    need_pkg; apk=${1:?apk}
    sha256sum "$apk" | tee -a "$OUT/final.log"
    adb uninstall "$PKG" >/dev/null 2>&1 || true
    adb logcat -c; adb install "$apk" | tee -a "$OUT/final.log"
    adb shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$PKG" | tee "$OUT/coldstart.txt" ;;
  update-prev)   # step 1 of update test: clean install of the previous released version
    need_pkg; prev=${1:?prev.apk}
    adb uninstall "$PKG" >/dev/null 2>&1 || true
    sha256sum "$prev" | tee -a "$OUT/final.log"; adb install "$prev" | tee -a "$OUT/final.log"
    log "previous version installed — now sign in and create data (incl. one pending offline write), then run: update <new.apk>" ;;
  update)        # step 2: install the release candidate over it (same signing key)
    need_pkg; new=${1:?new.apk}
    sha256sum "$new" | tee -a "$OUT/final.log"
    adb install -r "$new" 2>&1 | tee -a "$OUT/final.log" | grep -q Success || { echo "FINDING P0: update install failed"; exit 1; }
    adb shell dumpsys package "$PKG" | grep -E "versionName|versionCode|lastUpdateTime" | tee -a "$OUT/final.log"
    log "now verify: session kept, data intact, outbox flushed, no re-onboarding" ;;
  evidence)
    n=${1:?name}; adb exec-out screencap -p > "$OUT/$n.png"; adb exec-out uiautomator dump /dev/tty > "$OUT/$n.xml" 2>/dev/null || true; log "shot $n" ;;
  record)
    n=${1:?name}; t=${2:-180}; adb shell screenrecord --bit-rate 4000000 --time-limit "$t" "/sdcard/$n.mp4" || true
    adb pull "/sdcard/$n.mp4" "$OUT/$n.mp4" >/dev/null && adb shell rm "/sdcard/$n.mp4"; log "video $n" ;;
  logscan)
    need_pkg
    adb logcat -d '*:E' > "$OUT/logcat-errors.txt"; adb logcat -d -b crash > "$OUT/logcat-crash.txt" || true
    adb shell dumpsys activity exit-info "$PKG" > "$OUT/exit-info.txt" 2>/dev/null || true
    pat='FATAL EXCEPTION|ANR in '"$PKG"'|ReactNativeJS|Unhandled promise|SQLiteException|StrictMode|Process: '"$PKG"
    hits=$(grep -cE "$pat" "$OUT/logcat-errors.txt" "$OUT/logcat-crash.txt" | awk -F: '{s+=$2} END{print s+0}')
    grep -nE "$pat" "$OUT/logcat-errors.txt" "$OUT/logcat-crash.txt" | head -50 || true
    pii=$(grep -cE 'eyJ[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}' "$OUT/logcat-errors.txt" || true)
    exits=$(grep -cE 'reason=(4|5|6)[^0-9]' "$OUT/exit-info.txt" || true)   # 4 CRASH, 5 CRASH_NATIVE, 6 ANR
    echo "app error/crash lines: $hits · possible tokens/emails in error log: $pii · crash/ANR exits: $exits"
    [ "$hits" = 0 ] && [ "${pii:-0}" = 0 ] && [ "${exits:-0}" = 0 ] || { echo "FINDING: see $OUT"; exit 1; } ;;
  perf)
    need_pkg
    adb shell dumpsys gfxinfo "$PKG" > "$OUT/gfxinfo.txt"
    grep -E "Total frames rendered|Janky frames|90th percentile|99th percentile" "$OUT/gfxinfo.txt" | head -4
    adb shell dumpsys meminfo "$PKG" | grep -E "TOTAL( PSS)?:" | head -1
    echo "(reset counters before a flow with: adb shell dumpsys gfxinfo $PKG reset)" ;;
  stop) # only the emulator WE started (serial from ANDROID_SERIAL / pid file); never other agents'
    adb -s "$SERIAL" emu kill || true; rm -f "qa/final/${SERIAL}.pid" "qa/final/emulator-${SERIAL#emulator-}.pid" ;;
  *) sed -n '2,6p' "$0"; exit 2 ;;
esac
