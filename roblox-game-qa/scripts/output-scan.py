#!/usr/bin/env python3
"""output-scan.py — scan Roblox Output / F9 / MCP play logs for findings.

Input: one or more text files (Output copied from Studio, F9 export, or the JSON written by studio-mcp.py),
or '-' for stdin. Each matching line is classified with a default severity; the summary goes to stdout and,
with --json FILE, to a machine-readable list. Exit 1 if any P0/P1 hit (so it can gate a script).
Allowed noise is filtered with --allow REGEX (repeatable), e.g. --allow '^\\[analytics\\]'.
"""
import json, re, sys, argparse

RULES = [  # (severity, label, regex)
    ("P0", "script error", r"(?i)\b(error|exception)\b.*(script|:\d+:)|attempt to (index|call|perform|compare)|stack (begin|traceback)"),
    ("P1", "infinite yield", r"(?i)infinite yield possible"),
    ("P1", "asset failed", r"(?i)failed to load|asset (is not|not) (found|approved|trusted)|does not have permission|sound failed|animation failed"),
    ("P1", "datastore", r"(?i)datastore|request was throttled|budget"),
    ("P1", "remote/http", r"(?i)remote(event|function).*(error|exhausted|queue)|httpservice.*(error|not enabled)"),
    ("P2", "deprecated", r"(?i)deprecated|wait\(\) is|use task\."),
    ("P2", "warning", r"(?i)\bwarn(ing)?\b"),
]

def lines(paths):
    for p in paths:
        f = sys.stdin if p == "-" else open(p, encoding="utf-8", errors="replace")
        txt = f.read()
        try:  # studio-mcp.py JSON: {"logs":[{"level","message"}]}
            data = json.loads(txt)
            for item in (data if isinstance(data, list) else [data]):
                for l in item.get("logs", []):
                    yield p, f"[{l.get('level','')}] {l.get('message','')}"
            continue
        except Exception:
            pass
        for l in txt.splitlines():
            yield p, l

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+")
    ap.add_argument("--allow", action="append", default=[]); ap.add_argument("--json")
    a = ap.parse_args(); allow = [re.compile(x) for x in a.allow]
    hits, seen = [], set()
    for src, l in lines(a.files):
        s = l.strip()
        if not s or any(r.search(s) for r in allow):
            continue
        for sev, label, rx in RULES:
            if re.search(rx, s):
                key = (label, re.sub(r"\d+", "#", s)[:160])
                if key not in seen:
                    seen.add(key); hits.append({"severity": sev, "label": label, "line": s[:300], "file": src})
                break
    for h in hits:
        print(f"{h['severity']} [{h['label']}] {h['line']}")
    c = {k: sum(h["severity"] == k for h in hits) for k in ("P0", "P1", "P2")}
    print(f"output-scan: P0 {c['P0']} · P1 {c['P1']} · P2 {c['P2']} (unique lines; --allow filters intended noise)")
    if a.json:
        json.dump(hits, open(a.json, "w"), indent=1, ensure_ascii=False)
    sys.exit(1 if c["P0"] or c["P1"] else 0)

if __name__ == "__main__":
    main()
