#!/usr/bin/env bash
# Matrix sweep: screenshots + UI dumps of every screen for every config.
# Env:
#   APP_ID   (required) Android package, e.g. com.example.app
#   SCREENS  qa/screens.txt with "name|deeplink" lines, OR a Maestro flow (*.yaml) that takes screenshots
#   OUT      output dir (default qa/sweep/<timestamp>)
#   LOCALES  default "en-US pt-BR es-419 pt-PT"     THEMES default "light dark"
#   FONTS    default "1.0 1.3 2.0"                   SIZES  default "default small"
#   SETTLE   seconds to wait after opening a screen (default 2)
#   MAESTRO_LANG_FLOW optional Maestro flow to set the in-app language (receives -e LANG=<locale>)
# Output: $OUT/<theme>_<locale>_f<font>_<size>/<screen>.png + .xml, $OUT/manifest.tsv, logcat-crash.txt
set -euo pipefail
: "${APP_ID:?set APP_ID}"; : "${SCREENS:?set SCREENS}"
OUT="${OUT:-qa/sweep/$(date +%F-%H%M)}"
LOCALES="${LOCALES:-en-US pt-BR es-419 pt-PT}"; THEMES="${THEMES:-light dark}"
FONTS="${FONTS:-1.0 1.3 2.0}"; SIZES="${SIZES:-default small}"; SETTLE="${SETTLE:-2}"
HERE="$(cd "$(dirname "$0")" && pwd)"; A="adb ${ADB_SERIAL:+-s $ADB_SERIAL}"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
$A get-state >/dev/null || { echo "no device"; exit 1; }
"$HERE/adb-env.sh" save; trap '"$HERE/adb-env.sh" reset' EXIT
"$HERE/adb-env.sh" anim off
$A logcat -b crash -c || true
printf "config\ttheme\tlocale\tfont\tsize\tscreen\tpng\txml\n" > "$OUT/manifest.tsv"
density() { $A shell wm density | tr -d '\r' | awk -F': ' '/Override/{o=$2} /Physical/{p=$2} END{print (o?o:p)}'; }

for theme in $THEMES; do for loc in $LOCALES; do for font in $FONTS; do for size in $SIZES; do
  cfg="${theme}_${loc}_f${font}_${size}"; dir="$OUT/$cfg"; mkdir -p "$dir"
  echo "== $cfg"
  "$HERE/adb-env.sh" theme "$theme" >/dev/null
  "$HERE/adb-env.sh" font "$font"; "$HERE/adb-env.sh" size "$size"
  $A shell am force-stop "$APP_ID"
  "$HERE/adb-env.sh" locale "$APP_ID" "$loc" >/dev/null || echo "warn: set-app-locales failed (Android <13?)"
  if [ -n "${MAESTRO_LANG_FLOW:-}" ]; then maestro ${ADB_SERIAL:+--device $ADB_SERIAL} test -e LANG="$loc" "$MAESTRO_LANG_FLOW" >/dev/null; fi
  echo "density=$(density)" > "$dir/env.txt"
  if [[ "$SCREENS" == *.yaml || "$SCREENS" == *.yml ]]; then
    # Maestro mode: run from $dir so takeScreenshot files land there; dump UI is up to the flow.
    abs="$(cd "$(dirname "$SCREENS")" && pwd)/$(basename "$SCREENS")"
    (cd "$dir" && maestro ${ADB_SERIAL:+--device $ADB_SERIAL} test -e APP_ID="$APP_ID" "$abs") || echo "warn: sweep flow failed in $cfg" | tee -a "$OUT/errors.txt"
    for f in "$dir"/*.png; do [ -e "$f" ] || continue; n=$(basename "$f" .png)
      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$cfg" "$theme" "$loc" "$font" "$size" "$n" "$f" "" >> "$OUT/manifest.tsv"; done
  else
    $A shell monkey -p "$APP_ID" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep $((SETTLE+3))
    while IFS="|" read -r name link <&3; do
      [[ -z "$name" || "$name" == \#* ]] && continue
      if [ -n "${link:-}" ]; then $A shell am start -W -a android.intent.action.VIEW -d "$link" "$APP_ID" >/dev/null 2>&1 || true; fi
      sleep "$SETTLE"
      $A exec-out screencap -p > "$dir/$name.png"
      $A exec-out uiautomator dump /dev/tty 2>/dev/null | sed 's/UI hierchary dumped to.*//' > "$dir/$name.xml" || true
      printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$cfg" "$theme" "$loc" "$font" "$size" "$name" "$dir/$name.png" "$dir/$name.xml" >> "$OUT/manifest.tsv"
    done 3< "$SCREENS"
  fi
done; done; done; done
$A logcat -b crash -d > "$OUT/logcat-crash.txt" || true
echo "done → $OUT  (next: python3 $HERE/sweep-check.py $OUT)"
