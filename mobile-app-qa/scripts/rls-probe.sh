#!/usr/bin/env bash
# RLS / IDOR probe against a STAGING Supabase project with QA accounts only. Never use the service role.
# Env (from your secret store; never echoed): SUPABASE_URL, SUPABASE_ANON_KEY, TOKEN (access token of the
# attacker account, e.g. stranger C). Args: <table> <space_column> <victim_space_id> [victim_row_id]
# Optional BODY = a complete valid JSON row for <table> with the victim space (otherwise a 400 from a
# NOT NULL column can look like a pass — check the error text). Prints only HTTP status and row counts. Expected: 0 rows readable, every write rejected/0 rows.
set -euo pipefail
: "${SUPABASE_URL:?}" "${SUPABASE_ANON_KEY:?}" "${TOKEN:?}"
T="$1"; COL="$2"; SID="$3"; RID="${4:-}"
H=(-H "apikey: $SUPABASE_ANON_KEY" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")
req() { curl -s -o /tmp/rls-probe.$$ -w '%{http_code}' "${H[@]}" "$@"; }
rows() { python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print(len(d) if isinstance(d,list) else "n/a")' /tmp/rls-probe.$$ 2>/dev/null || echo n/a; }
fail=0
c=$(req "$SUPABASE_URL/rest/v1/$T?select=*&$COL=eq.$SID"); n=$(rows); echo "READ  $T $COL=victim → $c rows=$n"; [ "$n" = 0 ] || [ "$c" -ge 400 ] || fail=1
c=$(req -X POST -H "Prefer: return=representation" "$SUPABASE_URL/rest/v1/$T" -d "${BODY:-{\"$COL\":\"$SID\"}}"); echo "INSERT into victim space → $c $(grep -o '"message":"[^"]*"' /tmp/rls-probe.$$ | head -1)"; [ "$c" -ge 400 ] || fail=1
if [ -n "$RID" ]; then
  c=$(req -X PATCH -H "Prefer: return=representation" "$SUPABASE_URL/rest/v1/$T?id=eq.$RID" -d "{\"$COL\":\"$SID\"}"); n=$(rows); echo "UPDATE victim row → $c rows=$n"; [ "$n" = 0 ] || [ "$c" -ge 400 ] || fail=1
  c=$(req -X DELETE -H "Prefer: return=representation" "$SUPABASE_URL/rest/v1/$T?id=eq.$RID"); n=$(rows); echo "DELETE victim row → $c rows=$n"; [ "$n" = 0 ] || [ "$c" -ge 400 ] || fail=1
fi
rm -f /tmp/rls-probe.$$
[ $fail = 0 ] && echo "PASS $T" || { echo "FINDING P0: RLS breach on $T"; exit 1; }
