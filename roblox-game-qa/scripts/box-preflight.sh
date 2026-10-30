#!/usr/bin/env bash
# box-preflight.sh — RAM/process pre-flight and watchdog for heavy jobs on a SHARED machine.
# Companion to box-reserve.sh (the shared schedule + locks; canonical copy in mobile-app-qa/scripts/,
# installed at $BOX_SHARED/box-reserve.sh). This script never books, locks or kills anything of others.
#
#   box-preflight.sh check -r studio,studio-client [-n 1]   can I start these now? (exit 0 yes · 5 no RAM · 6 port busy)
#   box-preflight.sh watch --pid N [--log F] [--kill]      sample every 10 s; when free RAM < headroom: warn,
#                                                           and with --kill stop ONLY pid N (your own job)
#   box-preflight.sh procs                                  heavy processes on the box (look, never kill others')
#
# Resources and default RAM estimates (MB, override with env EST_<NAME>, e.g. EST_STUDIO=3000):
#   studio 2600 (one Studio process: edit session, or each Play/Server/Client window)
#   studio-client 2600 (each extra Clients-and-Servers client) · emulator 4096 · build 3072 · lune 300 · mcp 200
# Env: HEADROOM_MB (default 2048: free RAM that must remain AFTER your job; there is no swap),
#      BOX_SHARED (default /home/box/shared), MCP_PORT (default 44755, the single Studio MCP bridge port).
set -uo pipefail
SH=${BOX_SHARED:-/home/box/shared}; HEAD=${HEADROOM_MB:-2048}; PORT=${MCP_PORT:-44755}
cmd=${1:-}; shift || true
R=""; N=1; PID=""; LOG=""; KILL=0; INT=${INTERVAL:-10}
while [ $# -gt 0 ]; do case "$1" in
  -r) R=$2; shift 2;; -n) N=$2; shift 2;; --pid) PID=$2; shift 2;; --log) LOG=$2; shift 2;;
  --kill) KILL=1; shift;; *) echo "unknown arg $1"; exit 2;; esac; done
avail(){ awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo; }
swap(){ awk '/SwapTotal/{print int($2/1024)}' /proc/meminfo; }
est(){ local n=${1^^}; n=${n//-/_}; local v="EST_$n"; [ -n "${!v:-}" ] && { echo "${!v}"; return; }
  case "$1" in studio|studio-client) echo 2600;; emulator) echo 4096;; build) echo 3072;; lune) echo 300;;
    mcp) echo 200;; *) echo 1024;; esac; }
HEAVY='RobloxStudio|StudioMCP|rbx-studio-mcp|vinegar|wineserver|qemu-system|emulator64|/emulator/emulator|gradle|kotlin-daemon|maestro|java '
procs(){ echo "== heavy processes (pid user age rss cmd)"
  ps -eo pid=,user=,etimes=,rss=,args= --sort=-rss | grep -E "$HEAVY" | grep -v -E 'grep|box-preflight' | head -15 |
    awk '{printf "%s %s %ss %dMB ",$1,$2,$3,$4/1024; for(i=5;i<=NF&&i<9;i++) printf "%s ",substr($i,1,60); print ""}'
  local s; s=$(pgrep -fc 'RobloxStudioBeta' 2>/dev/null || true); echo "Studio processes: ${s:-0}"
  local q; q=$(pgrep -fc 'qemu-system' 2>/dev/null || true); echo "emulators (qemu): ${q:-0}"; }
case "$cmd" in
  check)
    [ -n "$R" ] || { echo "missing -r (e.g. -r studio,studio-client)"; exit 2; }
    need=0; for r in ${R//,/ }; do need=$(( need + $(est "$r") )); done; need=$(( need * N ))
    a=$(avail); echo "== RAM: available ${a} MB · swap $(swap) MB · job needs ~${need} MB · headroom ${HEAD} MB"
    procs
    if [ -x "$SH/box-reserve.sh" ]; then echo "== schedule"; "$SH/box-reserve.sh" status | sed -n '/== locks/,$p'; else echo "(no $SH/box-reserve.sh: no shared schedule found)"; fi
    rc=0
    if [ $(( a - need )) -lt "$HEAD" ]; then
      echo "NO-GO: ${a} - ${need} < ${HEAD} MB headroom. Wait for the running jobs, shrink the job (fewer clients), or book another slot."; rc=5; fi
    case ",$R," in *,studio*|*,mcp,*)
      if (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null) | grep -q ":$PORT "; then
        echo "MCP port $PORT already listening: another Studio MCP bridge is up (one bridge per box). Coordinate before starting yours."; [ $rc = 0 ] && rc=6; fi;; esac
    [ $rc = 0 ] && echo "GO: enough RAM for $R ×$N (still check the schedule above and hold the lock)."
    exit $rc ;;
  watch)
    [ -n "$PID" ] || { echo "missing --pid (your own job's pid)"; exit 2; }
    echo "watching pid $PID; stop line at ${HEAD} MB available"
    while kill -0 "$PID" 2>/dev/null; do
      a=$(avail); top=$(ps -eo rss=,comm= --sort=-rss | head -4 | awk '{printf "%s:%dMB ",$2,$1/1024}')
      line="$(date +%H:%M:%S) avail=${a}MB | $top"
      [ -n "$LOG" ] && echo "$line" >> "$LOG"
      if [ "$a" -lt "$HEAD" ]; then echo "LOW RAM: $line"
        [ $KILL = 1 ] && { echo "stopping own pid $PID"; kill "$PID"; exit 7; }; fi
      sleep "$INT"; done; echo "pid $PID ended" ;;
  procs) echo "RAM available $(avail) MB"; procs ;;
  *) sed -n '2,14p' "$0"; exit 2 ;;
esac
