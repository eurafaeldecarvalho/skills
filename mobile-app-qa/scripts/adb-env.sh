#!/usr/bin/env bash
# One-line device toggles for QA, with reset. Usage:
#   adb-env.sh theme dark|light|auto        adb-env.sh locale <pkg> pt-BR|""
#   adb-env.sh font 1.0|1.3|2.0             adb-env.sh size default|small|large
#   adb-env.sh nav gesture|threebutton      adb-env.sh net on|off
#   adb-env.sh dka on|off (don't keep activities)   adb-env.sh anim off|on
#   adb-env.sh clock 24|12                  adb-env.sh save | reset
set -euo pipefail
A="adb ${ADB_SERIAL:+-s $ADB_SERIAL}"
STATE="${QA_STATE_FILE:-/tmp/adb-env.$(${A} get-serialno 2>/dev/null || echo dev).state}"
ash() { $A shell "$@" | tr -d '\r'; }
case "${1:-}" in
  save)
    { echo "font_scale=$(ash settings get system font_scale)"
      echo "time_12_24=$(ash settings get system time_12_24)"
      echo "dka=$(ash settings get global always_finish_activities)"
      echo "night=$(ash cmd uimode night | awk '{print $NF}')"
      for s in window_animation_scale transition_animation_scale animator_duration_scale; do echo "$s=$(ash settings get global $s)"; done
    } > "$STATE"; echo "saved $STATE";;
  reset)
    [ -f "$STATE" ] || { echo "no saved state; resetting to defaults"; }
    font=1.0; night=auto; t=null; dka=0; w=1; tr=1; an=1
    if [ -f "$STATE" ]; then
      font=$(grep ^font_scale= "$STATE" | cut -d= -f2); night=$(grep ^night= "$STATE" | cut -d= -f2)
      t=$(grep ^time_12_24= "$STATE" | cut -d= -f2); dka=$(grep ^dka= "$STATE" | cut -d= -f2)
      w=$(grep ^window_animation_scale= "$STATE" | cut -d= -f2); tr=$(grep ^transition_animation_scale= "$STATE" | cut -d= -f2)
      an=$(grep ^animator_duration_scale= "$STATE" | cut -d= -f2)
    fi
    [ "$font" = null ] && font=1.0
    ash settings put system font_scale "$font"; ash cmd uimode night "$night" >/dev/null
    [ "$t" != null ] && ash settings put system time_12_24 "$t"
    [ "$dka" = null ] && dka=0; ash settings put global always_finish_activities "$dka"
    for p in "window_animation_scale:$w" "transition_animation_scale:$tr" "animator_duration_scale:$an"; do
      v=${p#*:}; [ "$v" = null ] && v=1; ash settings put global "${p%%:*}" "$v"; done
    ash wm size reset; ash wm density reset
    ash cmd connectivity airplane-mode disable || true
    echo "reset done";;
  theme) case "$2" in dark) ash cmd uimode night yes;; light) ash cmd uimode night no;; *) ash cmd uimode night auto;; esac;;
  locale) ash cmd locale set-app-locales "$2" --locales "${3:-}"; ash cmd locale get-app-locales "$2" || true;;
  font) ash settings put system font_scale "$2";;
  size) case "$2" in small) ash wm size 720x1280; ash wm density 320;; large) ash wm size 1440x3120; ash wm density 560;; *) ash wm size reset; ash wm density reset;; esac;;
  nav) ash cmd overlay enable-exclusive --category "com.android.internal.systemui.navbar.$2" || ash cmd overlay enable "com.android.internal.systemui.navbar.$2";;
  net) [ "$2" = off ] && ash cmd connectivity airplane-mode enable || ash cmd connectivity airplane-mode disable;;
  dka) ash settings put global always_finish_activities "$([ "$2" = on ] && echo 1 || echo 0)";;
  anim) v=$([ "$2" = off ] && echo 0 || echo 1); for s in window_animation_scale transition_animation_scale animator_duration_scale; do ash settings put global $s $v; done;;
  clock) ash settings put system time_12_24 "$2";;
  *) sed -n '2,8p' "$0"; exit 1;;
esac
