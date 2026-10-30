#!/usr/bin/env bash
# Launch/splash capture: screenrecord every launch and extract frames for sweep-check.py --splash.
# Env:
#   APP_ID   (required) Android package (release build already installed)
#   OUT      output dir (default qa/splash/<timestamp>)
#   PROFILES "name:WxH:density ..."  default "small:720x1280:320 phone:1080x2400:420 tablet:1600x2560:320"
#            (use "native::" to keep the device's own size/density)
#   THEMES   default "light dark"         STARTS default "cold warm hot" (hot: no system splash expected)
#   REC_SECS seconds recorded per launch (default 5)   FPS frames per second extracted (default 30)
#   BOX_PROJECT (required) your emulator reservation (box-reserve.sh); BOX_FORCE=1 skips the check
# Output: $OUT/<profile>_<theme>_<start>/{launch.mp4, frames/NNNN.png, first-screen.png, env.txt, am-start.txt}
# Needs adb, ffmpeg (apt install ffmpeg). Runs with animations ON (what users see); restores the device on exit.
set -euo pipefail
: "${APP_ID:?set APP_ID}"
OUT="${OUT:-qa/splash/$(date +%F-%H%M)}"
PROFILES="${PROFILES:-small:720x1280:320 phone:1080x2400:420 tablet:1600x2560:320}"
THEMES="${THEMES:-light dark}"; STARTS="${STARTS:-cold warm hot}"; REC_SECS="${REC_SECS:-5}"; FPS="${FPS:-30}"
HERE="$(cd "$(dirname "$0")" && pwd)"; A="adb ${ADB_SERIAL:+-s $ADB_SERIAL}"
command -v ffmpeg >/dev/null || { echo "ffmpeg missing (apt install ffmpeg)"; exit 2; }
$A get-state >/dev/null || { echo "no device"; exit 1; }
if [ "${BOX_FORCE:-0}" != 1 ]; then
  [ -n "${BOX_PROJECT:-}" ] || { echo "set BOX_PROJECT and reserve the box first (scripts/box-reserve.sh)"; exit 4; }
  "$HERE/box-reserve.sh" check -p "$BOX_PROJECT" -r emulator || { echo "refusing: no valid emulator reservation"; exit 4; }
fi
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
ACT=$($A shell cmd package resolve-activity --brief -c android.intent.category.LAUNCHER "$APP_ID" | tr -d '\r' | tail -1)
case "$ACT" in */*) ;; *) echo "cannot resolve launcher activity for $APP_ID"; exit 1;; esac
"$HERE/adb-env.sh" save; trap '$A shell wm size reset >/dev/null; $A shell wm density reset >/dev/null; "$HERE/adb-env.sh" reset' EXIT
"$HERE/adb-env.sh" anim on
density() { $A shell wm density | tr -d '\r' | awk -F': ' '/Override/{o=$2} /Physical/{p=$2} END{print (o?o:p)}'; }
size() { $A shell wm size | tr -d '\r' | awk -F': ' '/Override/{o=$2} /Physical/{p=$2} END{print (o?o:p)}'; }
for prof in $PROFILES; do
  IFS=: read -r pname psize pdens <<<"$prof"
  if [ -n "$psize" ]; then $A shell wm size "$psize"; $A shell wm density "$pdens"; else $A shell wm size reset; $A shell wm density reset; fi
  for theme in $THEMES; do
    "$HERE/adb-env.sh" theme "$theme" >/dev/null; sleep 1
    for start in $STARTS; do
      cfg="${pname}_${theme}_${start}"; dir="$OUT/$cfg"; rm -rf "$dir"; mkdir -p "$dir/frames"; echo "== $cfg"
      # prepare the start kind: the app must have been launched once for warm/hot
      $A shell am force-stop "$APP_ID"
      if [ "$start" != cold ]; then
        $A shell am start -W -n "$ACT" >/dev/null; sleep 4
        if [ "$start" = warm ]; then $A shell input keyevent KEYCODE_BACK; else $A shell input keyevent KEYCODE_HOME; fi
        sleep 2
      fi
      { echo "density=$(density)"; echo "size=$(size)"; echo "theme=$theme"; echo "start=$start"; echo "profile=$pname"; echo "fps=$FPS"; echo "pre_secs=0.6"; } > "$dir/env.txt"
      $A shell rm -f /sdcard/qa-splash.mp4
      $A shell screenrecord --bit-rate 8000000 --time-limit "$REC_SECS" /sdcard/qa-splash.mp4 & rec=$!
      sleep 0.8   # screenrecord needs a moment before the first frame
      $A shell am start -W -n "$ACT" | tr -d '\r' > "$dir/am-start.txt" || true
      wait "$rec" || true; sleep 0.5
      $A pull /sdcard/qa-splash.mp4 "$dir/launch.mp4" >/dev/null
      ffmpeg -loglevel error -i "$dir/launch.mp4" -vf "fps=$FPS" "$dir/frames/%04d.png"
      last=$(ls "$dir/frames" | tail -1); [ -n "$last" ] && cp "$dir/frames/$last" "$dir/first-screen.png"
      grep -E 'TotalTime|WaitTime|LaunchState' "$dir/am-start.txt" | sed 's/^/  /' || true
    done
  done
done
$A shell rm -f /sdcard/qa-splash.mp4
echo "done → $OUT  (next: python3 $HERE/sweep-check.py --splash $OUT --logo <logo.png>)"
