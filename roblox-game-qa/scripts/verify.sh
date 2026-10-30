#!/usr/bin/env bash
# verify.sh — headless Audit gate (pass 1) for a Rojo/Luau project. Run from the project root.
# Steps: luau-compile every .luau · rojo build · luau-lsp analyze (sourcemap + Roblox defs) · selene ·
# stylua --check · release-flag grep · Lune tests (3× with FLAKE=3).
# Env: PROJECT (default.project.json) SRC (src) TESTS (tests) LUNE_ENTRY (tests/run or tests/rodar)
#      STATIC=required  → a missing tool is a failure (use it in the gate; default only skips with a note)
#      FLAGS_RE         → regex of debug flags that must not be true in the release config
#      FLAKE=3          → run the Lune suite N times; any failure in any run = flaky = a finding
# Exit 0 only if everything that ran is green.
set -uo pipefail
PROJECT=${PROJECT:-default.project.json}; SRC=${SRC:-src}; TESTS=${TESTS:-tests}; FLAKE=${FLAKE:-1}
FLAGS_RE=${FLAGS_RE:-'(DEBUG|SKIP_[A-Z_]+|FAST_TIMERS|GOD_MODE|FREE_[A-Z_]+|ANALYTICS_DEBUG)[[:space:]]*=[[:space:]]*true'}
OUT=${OUT:-/tmp/verify-$(basename "$PWD")}; mkdir -p "$OUT"
fail=0; step(){ printf '\n== %s\n' "$1"; }
missing(){ if [ "${STATIC:-}" = required ]; then echo "MISSING: $1"; fail=1; else echo "(skipped: $1 not installed)"; fi; }
have(){ command -v "$1" >/dev/null 2>&1; }

step "luau-compile"
LC=${LUAU_COMPILE:-$(command -v luau-compile || echo /tmp/tools/luau-compile)}
if [ -x "$LC" ]; then n=0; bad=0
  while IFS= read -r f; do n=$((n+1)); "$LC" "$f" >/dev/null 2>"$OUT/lc.err" || { echo "FAIL $f"; cat "$OUT/lc.err"; bad=$((bad+1)); }; done \
    < <(find "$SRC" "$TESTS" -name '*.luau' -o -name '*.lua' 2>/dev/null | sort)
  echo "$n files, $bad failures"; [ $bad = 0 ] || fail=1
else missing "luau-compile (github.com/luau-lang/luau releases)"; fi

step "rojo build"
if have rojo; then rojo build "$PROJECT" -o "$OUT/build.rbxlx" 2>&1 | tee "$OUT/rojo.log" | tail -3
  [ "${PIPESTATUS[0]}" = 0 ] || fail=1; grep -qiE 'warn|unknown|duplicate' "$OUT/rojo.log" && { echo "rojo warnings above = finding"; fail=1; }
else missing rojo; fi

step "luau-lsp analyze"
if have luau-lsp && have rojo; then
  defs=${LUAU_DEFS:-/tmp/tools/globalTypes.d.luau}
  [ -s "$defs" ] || { mkdir -p "$(dirname "$defs")"; curl -sSfL https://raw.githubusercontent.com/JohnnyMorganz/luau-lsp/main/scripts/globalTypes.d.luau -o "$defs"; }
  rojo sourcemap "$PROJECT" -o "$OUT/sourcemap.json" >/dev/null
  o=$(luau-lsp analyze --sourcemap="$OUT/sourcemap.json" --definitions="$defs" --platform=roblox "$SRC" 2>&1 | grep -v '^\[' || true)
  if [ -n "$o" ]; then echo "$o" | tail -40; echo "luau-lsp: errors"; fail=1; else echo "0 errors"; fi
else missing luau-lsp; fi

step "selene"
if have selene; then selene --display-style quiet "$SRC" || fail=1; else missing selene; fi

step "stylua --check"
if have stylua; then stylua --check "$SRC" "$TESTS" >/dev/null 2>&1 && echo ok || { echo "unformatted files (run stylua $SRC $TESTS)"; fail=1; }
else missing stylua; fi

step "release flags + leftovers"
hits=$(grep -rnE "$FLAGS_RE" "$SRC" 2>/dev/null || true)
[ -n "$hits" ] && { echo "$hits"; echo "debug flag ON in source = P1 before publish"; fail=1; } || echo "no debug flag set to true"
echo "print/warn calls: $(grep -rnE '^[^-]*\b(print|warn)\(' "$SRC" 2>/dev/null | wc -l) (review noisy ones)"

step "Lune tests ×$FLAKE"
entry=${LUNE_ENTRY:-$( [ -e "$TESTS/run.luau" ] && echo "$TESTS/run" || echo "$TESTS/rodar")}
if have lune && [ -e "$entry.luau" -o -e "$entry" ]; then
  for i in $(seq 1 "$FLAKE"); do lune run "$entry" > "$OUT/lune-$i.log" 2>&1 && echo "run $i: green" || { echo "run $i: RED (see $OUT/lune-$i.log)"; tail -15 "$OUT/lune-$i.log"; fail=1; }; done
else missing "lune or $entry"; fi

echo; [ $fail = 0 ] && echo "VERIFY: GREEN (logs in $OUT)" || echo "VERIFY: RED (logs in $OUT)"; exit $fail
