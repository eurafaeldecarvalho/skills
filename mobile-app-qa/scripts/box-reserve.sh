#!/usr/bin/env bash
# box-reserve.sh — reserve the shared machine before builds, emulators, Maestro, sweeps or the FINAL PASS.
# Several agents share ONE box (CPU, RAM, disk, Android SDK). Book a slot, hold a lock while you run,
# release it on exit (even on failure). Times are box-local (the box clock's zone), "YYYY-MM-DD HH:MM".
#
#   box-reserve.sh status                                   load + live locks + upcoming slots
#   box-reserve.sh reserve -p <project> -o <owner> -r emulator,build -s "2026-10-30 17:00" -e "2026-10-30 21:00" [-n note]
#   box-reserve.sh acquire -p <project> -r emulator [--pid N|0] [--force]   take the lock inside your slot
#                  (lock dies with --pid, default the caller; --pid 0 = held until the slot ends or release)
#   box-reserve.sh check   -p <project> -r emulator          exit 0 if you hold a valid lock (prints minutes left)
#   box-reserve.sh left    -p <project> -r emulator          minutes left in the held lock (0 if none)
#   box-reserve.sh release -p <project> -r emulator          drop the lock, mark the slot done
# Recurring slots are added by hand: | daily 09:00 | 12:00 | Project | Owner | all | recurring from 2026-10-31 | note |
# ("all" = exclusive use of the box; "cancelled" in Status disables a row).
# In scripts:  box-reserve.sh acquire -p "$BOX_PROJECT" -r emulator && trap 'box-reserve.sh release -p "$BOX_PROJECT" -r emulator' EXIT
# Env: BOX_SHARED (default /home/box/shared), MIN_FREE_GB (default 6), BOX_PROJECT (default for -p).
# Exit codes: 0 ok · 2 usage · 3 slot overlaps another booking · 4 lock held by someone else / no slot · 5 not enough free RAM
set -euo pipefail
SH=${BOX_SHARED:-/home/box/shared}; SCHED="$SH/box-schedule.md"; LOCKS="$SH/locks"; MIN_FREE_GB=${MIN_FREE_GB:-6}
mkdir -p "$LOCKS"
cmd=${1:-}; shift || true
P=${BOX_PROJECT:-}; O=${BOX_OWNER:-$(whoami)}; R=""; S=""; E=""; N=""; PID=$PPID; FORCE=0
while [ $# -gt 0 ]; do case "$1" in
  -p) P=$2; shift 2;; -o) O=$2; shift 2;; -r) R=$2; shift 2;; -s) S=$2; shift 2;; -e) E=$2; shift 2;;
  -n) N=$2; shift 2;; --pid) PID=$2; [ "$PID" = 0 ] && PID=""; shift 2;; --force) FORCE=1; shift;; *) echo "unknown arg $1"; exit 2;; esac; done
ts(){ date -d "$1" +%s; }
now=$(date +%s)
slug(){ echo "$1" | tr 'A-Z ' 'a-z-' | tr -cd 'a-z0-9-'; }
init(){ [ -f "$SCHED" ] || cat > "$SCHED" <<'H'
# Shared box schedule

One machine, many agents (same CPU, RAM, disk and Android SDK). Every agent that builds, boots an emulator,
runs Maestro/sweeps or any heavy job reserves a slot here first (`box-reserve.sh reserve`), takes the lock at
start (`acquire`, lock files in `locks/`) and releases it at the end (`release`, also on failure via `trap`).
Times are box-local "YYYY-MM-DD HH:MM" (BRT, America/Sao_Paulo). Overlapping a booked slot on the same
resource needs the other agent's explicit OK (message them); otherwise pick another slot.
Rules: one emulator per agent (`-memory 4096 -cores 4` max), Gradle `-Xmx3g --max-workers=2`, run under
`nice`/`ionice`, stop your own daemons/emulators when done, never kill another agent's processes, shared SDK
is add-only (never delete or overwrite cmdline-tools/platform-tools), prefix your AVDs/files with your project.
Script: /home/box/shared/box-reserve.sh (copy of mobile-app-qa/scripts/box-reserve.sh in the skills repo).
Recurring slots: `| daily HH:MM | HH:MM | … | recurring from YYYY-MM-DD |`; Resources `all` = exclusive use of the box.

| Start | End | Project | Owner | Resources | Status | Note |
|---|---|---|---|---|---|---|
H
}
rows(){ [ -f "$SCHED" ] && grep -E '^\| [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} \|' "$SCHED" || true; }
# Recurring rows: | daily HH:MM | HH:MM | Project | Owner | Resources | recurring from YYYY-MM-DD | Note |
daily_rows(){ [ -f "$SCHED" ] && grep -E '^\| daily [0-9]{2}:[0-9]{2} \|' "$SCHED" || true; }
# Concrete rows for one day: dated rows + daily rows expanded to that day (if started).
day_rows(){ local day=$1 l a b from st; rows
  daily_rows | while read -r l; do
    a=$(field "$l" 2); a=${a#daily }; b=$(field "$l" 3); st=$(field "$l" 7)
    from=$(echo "$st" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || echo 1970-01-01)
    case "$st" in cancelled*) continue;; esac
    [ "$(ts "$from")" -le "$(ts "$day")" ] || continue
    echo "$l" | awk -F'|' -v A="$day $a" -v B="$day $b" 'BEGIN{OFS="|"}{$2=" "A" ";$3=" "B" ";$7=" recurring ";print}'
  done; }
span_rows(){ local d=$1 last=$2; while [ "$(ts "$d")" -le "$(ts "$last")" ]; do day_rows "$d"; d=$(date -d "$d +1 day" +%F); done | sort -u; }
field(){ echo "$1" | awk -F'|' -v i="$2" '{gsub(/^ +| +$/,"",$i); print $i}'; }
inter(){ # do resource lists $1 and $2 intersect? ("all" matches anything)
  local a b; for a in ${1//,/ }; do for b in ${2//,/ }; do
    [ "$a" = "$b" ] || [ "$a" = all ] || [ "$b" = all ] && return 0; done; done; return 1; }
lockfile(){ echo "$LOCKS/$1.lock"; }
lock_live(){ # lock exists, pid alive, end not passed
  local f=$1; [ -f "$f" ] || return 1
  local lp le; lp=$(sed -n 's/^pid=//p' "$f"); le=$(sed -n 's/^end=//p' "$f")
  [ -n "$le" ] && [ "$(ts "$le")" -gt "$now" ] && { [ -z "$lp" ] || kill -0 "$lp" 2>/dev/null; }; }
need(){ for v in "$@"; do [ -n "${!v}" ] || { echo "missing -${v,,} (see header)"; exit 2; }; done; }
case "$cmd" in
  status)
    echo "== load ($(date '+%F %H:%M %Z'))"; echo "cores: $(nproc) · $(uptime | sed 's/.*load/load/')"
    free -h | sed -n '1,2p'; df -h /home 2>/dev/null | tail -1 | awk '{print "disk /home: "$4" free"}'
    echo "== heavy processes (all users; look, never kill others')"
    ps -eo pid,user,etimes,rss,comm,args --sort=-rss | grep -E 'qemu|emulator|gradle|java|node|maestro|kotlin' | grep -v grep | head -15 | awk '{printf "%s %s %ss %dMB %s\n",$1,$2,$3,$4/1024,$5}' || true
    command -v adb >/dev/null && { echo "== adb devices"; adb devices | tail -n +2; }
    echo "== locks"; for f in "$LOCKS"/*.lock; do [ -e "$f" ] || { echo "(none)"; break; }
      st=stale; lock_live "$f" && st=LIVE; echo "$(basename "$f" .lock): $st · $(tr '\n' ' ' < "$f")"; done
    echo "== slots (not finished)"; rows | while read -r l; do e=$(field "$l" 3); st=$(field "$l" 7)
      [ "$(ts "$e")" -gt "$now" ] && [ "$st" != done ] && [ "$st" != cancelled ] && echo "$l"; done
    echo "== recurring"; daily_rows; true ;;
  reserve)
    need P O R S E; init; s=$(ts "$S"); e=$(ts "$E"); [ "$e" -gt "$s" ] || { echo "end must be after start"; exit 2; }
    exec 9>"$LOCKS/.schedule"; flock 9
    conflict=0
    while read -r l; do [ -n "$l" ] || continue
      st=$(field "$l" 7); [ "$st" = done ] || [ "$st" = cancelled ] && continue
      [ "$(field "$l" 4)" = "$P" ] && continue
      ls_=$(ts "$(field "$l" 2)"); le=$(ts "$(field "$l" 3)")
      if [ "$s" -lt "$le" ] && [ "$ls_" -lt "$e" ] && inter "$R" "$(field "$l" 6)"; then echo "OVERLAP: $l"; conflict=1; fi
    done < <(span_rows "$(date -d "$S" +%F)" "$(date -d "$E" +%F)")
    if [ $conflict = 1 ] && [ $FORCE = 0 ]; then
      echo "Not booked. Message the owner(s) above, agree a slot, then book it (use --force only with their explicit OK)."; exit 3; fi
    echo "| $S | $E | $P | $O | $R | reserved | ${N//|//} |" >> "$SCHED"; echo "booked: $S → $E $P ($R)" ;;
  acquire)
    need P R; init
    slot=""; while read -r l; do [ -n "$l" ] || continue
      [ "$(field "$l" 4)" = "$P" ] || continue; st=$(field "$l" 7); [ "$st" = done ] || [ "$st" = cancelled ] && continue
      inter "$R" "$(field "$l" 6)" || continue
      [ "$(ts "$(field "$l" 2)")" -le "$now" ] && [ "$(ts "$(field "$l" 3)")" -gt "$now" ] && slot=$l; done < <(day_rows "$(date +%F)")
    if [ -z "$slot" ] && [ $FORCE = 0 ]; then echo "No slot for $P/$R covering now. Run 'status', book one with 'reserve'."; exit 4; fi
    end=$( [ -n "$slot" ] && field "$slot" 3 || date -d '+1 hour' '+%F %H:%M')
    avail=$(free -g | awk '/Mem:/{print $7}')
    if [ "$avail" -lt "$MIN_FREE_GB" ] && [ $FORCE = 0 ]; then echo "Only ${avail}G RAM available (< $MIN_FREE_GB G). Someone is still running; check 'status', don't kill their processes."; exit 5; fi
    exec 9>"$LOCKS/.schedule"; flock 9
    for r in ${R//,/ }; do f=$(lockfile "$r")
      if lock_live "$f" && [ "$(sed -n 's/^project=//p' "$f")" != "$P" ]; then echo "LOCKED by: $(tr '\n' ' ' < "$f")"; exit 4; fi
      printf 'project=%s\nowner=%s\nstart=%s\nend=%s\npid=%s\nhost=%s\n' "$P" "$O" "$(date '+%F %H:%M')" "$end" "$PID" "$(hostname)" > "$f"
    done
    [ -n "$slot" ] && sed -i "s#^| $(field "$slot" 2) | $(field "$slot" 3) | $P |\(.*\)| reserved |#| $(field "$slot" 2) | $(field "$slot" 3) | $P |\1| active |#" "$SCHED"
    echo "acquired $R for $P until $end ($(( ($(ts "$end")-now)/60 )) min)" ;;
  check|left)
    need P R; min=999999
    for r in ${R//,/ }; do f=$(lockfile "$r")
      if ! lock_live "$f" || [ "$(sed -n 's/^project=//p' "$f")" != "$P" ]; then
        [ "$cmd" = left ] && { echo 0; exit 0; }; echo "no valid $r lock for $P (run acquire inside a booked slot)"; exit 4; fi
      m=$(( ($(ts "$(sed -n 's/^end=//p' "$f")")-now)/60 )); [ $m -lt $min ] && min=$m; done
    [ "$cmd" = left ] && echo "$min" || echo "ok: $P holds $R · $min min left" ;;
  release)
    need P R
    for r in ${R//,/ }; do f=$(lockfile "$r")
      [ -f "$f" ] && [ "$(sed -n 's/^project=//p' "$f")" = "$P" ] && rm -f "$f"; done
    [ -f "$SCHED" ] && sed -i -E "s#^(\| [^|]+ \| [^|]+ \| $P \|.*\| )active( \|.*)#\1done\2#" "$SCHED"
    echo "released $R for $P" ;;
  *) sed -n '2,20p' "$0"; exit 2 ;;
esac
