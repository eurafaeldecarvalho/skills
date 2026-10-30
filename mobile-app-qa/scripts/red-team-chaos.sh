#!/usr/bin/env bash
# Red-team chaos helpers (emulator or dedicated QA phone only). Usage:
#   APP_ID=com.example.app OUT=qa/red-team/iter3 red-team-chaos.sh monkey [events] [seed...]
#   red-team-chaos.sh trim                 # RUNNING_CRITICAL in fg, then COMPLETE in bg
#   red-team-chaos.sh storage low|reset    # force the low-storage state
#   red-team-chaos.sh clock +2y|-2y|tz <Area/City>|auto   (verify support on your image)
#   red-team-chaos.sh rotate | backspam | killmid | clear | revoke <permission>
# Every run appends to $OUT/attempts.log; crashes are grepped from logcat at the end of each step.
set -euo pipefail
A="adb ${ADB_SERIAL:+-s $ADB_SERIAL}"; APP_ID="${APP_ID:?set APP_ID}"; OUT="${OUT:-qa/red-team/$(date +%F-%H%M)}"
mkdir -p "$OUT"; LOG="$OUT/attempts.log"
ash() { $A shell "$@" | tr -d '\r'; }
note() { echo "$(date +%T) $*" | tee -a "$LOG"; }
crashcheck() { local f="$OUT/crash-$1.txt"; $A logcat -b crash -d > "$f" || true
  if [ -s "$f" ] || $A logcat -d | grep -qE "ANR in $APP_ID|FATAL EXCEPTION"; then note "FINDING $1: crash/ANR → $f"; return 1; fi; note "ok $1"; }
fresh() { $A logcat -c || true; $A logcat -b crash -c || true; }
launch() { ash monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep 4; }
case "${1:-}" in
  monkey)
    ev="${2:-20000}"; shift $(( $# >= 2 ? 2 : 1 )); seeds=("$@"); [ ${#seeds[@]} -eq 0 ] && seeds=($RANDOM $RANDOM $RANDOM)
    printf '%s\n' "${seeds[@]}" >> "$OUT/seeds.txt"
    for s in "${seeds[@]}"; do fresh; note "monkey seed=$s events=$ev"
      ash monkey -p "$APP_ID" -s "$s" --throttle 80 --pct-syskeys 0 -v "$ev" > "$OUT/monkey-$s.txt" 2>&1 || true
      grep -qE "// CRASH|// NOT RESPONDING|Monkey aborted" "$OUT/monkey-$s.txt" && note "FINDING monkey seed=$s (see monkey-$s.txt)"
      crashcheck "monkey-$s" || true; done;;
  trim) fresh; launch; ash am send-trim-memory "$APP_ID" RUNNING_CRITICAL || true; sleep 2
        ash input keyevent 3; sleep 2; ash am send-trim-memory "$APP_ID" COMPLETE || true; launch; crashcheck trim || true;;
  storage) if [ "${2:-}" = reset ]; then ash cmd devicestoragemonitor reset || true; ash rm -f /sdcard/qa-fill || true
           else ash cmd devicestoragemonitor force-low -f || ash fallocate -l 4G /sdcard/qa-fill || true; fi; note "storage ${2:-low}";;
  clock) ash settings put global auto_time 0; ash settings put global auto_time_zone 0
         case "${2:-}" in
           auto) ash settings put global auto_time 1; ash settings put global auto_time_zone 1;;
           tz) ash cmd alarm set-timezone "$3" || ash setprop persist.sys.timezone "$3";;
           +2y|-2y) now=$(ash date +%s); d=$(( ${2:0:1}1 * 63072000 )); ash cmd alarm set-time "$(( (now + d) * 1000 ))" || note "set-time unsupported: use adb root + date";;
         esac; note "clock ${*:2}"; launch; crashcheck "clock-${2:-}" || true;;
  rotate) ash settings put system accelerometer_rotation 0
          for r in 1 0 3 0; do ash settings put system user_rotation $r; sleep 1.5; done; crashcheck rotate || true;;
  backspam) for _ in $(seq 20); do ash input keyevent 4; done; crashcheck backspam || true;;
  killmid) note "trigger the write now (Maestro/manual); killing in ${2:-1}s"; sleep "${2:-1}"; ash am kill "$APP_ID"; ash am force-stop "$APP_ID"; launch; crashcheck killmid || true;;
  clear) ash pm clear "$APP_ID"; launch; crashcheck clear || true;;
  revoke) ash pm revoke "$APP_ID" "$2"; note "revoked $2 (process is killed by Android)"; launch; crashcheck "revoke" || true;;
  *) sed -n '2,8p' "$0"; exit 1;;
esac
