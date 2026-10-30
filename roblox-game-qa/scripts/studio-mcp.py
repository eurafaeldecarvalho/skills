#!/usr/bin/env python3
"""studio-mcp.py — minimal stdio client for a Roblox Studio MCP server. Works with BOTH servers:
  * Studio's BUILT-IN server (Assistant ▸ … ▸ Manage MCP Servers ▸ "Enable Studio as MCP server"):
    Windows `cmd.exe /c %LOCALAPPDATA%\\Roblox\\mcp.bat`, macOS `.../RobloxStudio.app/Contents/MacOS/StudioMCP`.
    Tools: execute_luau{code, datamodel_type Edit|Server|Client}, start_stop_play, get_studio_state,
    get_console_output, screen_capture, list_roblox_studios, … — every call takes a studio_id.
  * the open-source Roblox/studio-rust-mcp-server (`rbx-studio-mcp --stdio`, needs its Studio plugin):
    run_code{command}, run_script_in_play_mode{code, mode, timeout}, start_stop_play, get_studio_mode, …

  studio-mcp.py tools [--json FILE]                 list tools (FILE gets the full schemas)
  studio-mcp.py call TOOL '{"json":"args"}'         call any tool
  studio-mcp.py batch CALLS.json                    run a JSON list in ONE server session: items are
                                                    ["tool", {args}, timeout?] | {"sleep": s} |
                                                    {"luau": FILE, "dm": "Edit|Server|Client", "sub": {"__N__": "2"},
                                                     "until": "TEXT", "every": 5, "max": 400}   (until = poll)
  studio-mcp.py edit FILE.luau                      run Luau in EDIT mode
  studio-mcp.py play FILE.luau [--timeout 120]      (open-source server only) run Luau on the play SERVER, then stop
  studio-mcp.py inject-client FILE.luau [--name QA_Client] / remove-client [--name QA_Client]
  studio-mcp.py run-pair CLIENT.luau SERVER.luau    (open-source server only) inject → play SERVER → remove

With the built-in server the play flow is: start_stop_play → execute_luau dm=Server / dm=Client → stop
(use `batch`). It has a real Client datamodel, so a client probe can run directly (no RemoteEvent relay).
studio_id is filled automatically (first studio, or the one whose name contains --studio TEXT).
Env: STUDIO_MCP_CMD = server command; a JSON list is safest on Windows, e.g.
  ["cmd.exe","/c","C:\\\\Users\\\\me\\\\AppData\\\\Local\\\\Roblox\\\\mcp.bat"]   (default: rbx-studio-mcp --stdio)
Output is saved as JSON with --out (default <tmp>/studio-mcp-last.json) for output-scan.py.
Shared machine: Studio is a heavy job — book it with box-reserve.sh and pass box-preflight.sh first.
"""
import argparse, json, os, queue, shlex, subprocess, sys, tempfile, threading, time

TMP = tempfile.gettempdir()
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles default to cp1252
except Exception:
    pass

def server_cmd():
    raw = os.environ.get("STUDIO_MCP_CMD", "rbx-studio-mcp --stdio").strip()
    if raw.startswith("["):
        return json.loads(raw)
    return shlex.split(raw, posix=(os.name != "nt"))  # posix shlex eats Windows backslashes

class Client:
    def __init__(self, studio_hint=None):
        self.p = subprocess.Popen(server_cmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=open(os.path.join(TMP, "studio-mcp-stderr.log"), "a", encoding="utf-8"),
                                  text=True, bufsize=1, encoding="utf-8", errors="replace")
        self.q = queue.Queue(); self.n = 0
        threading.Thread(target=lambda: [self.q.put(l) for l in self.p.stdout], daemon=True).start()
        r = self.req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                    "clientInfo": {"name": "roblox-game-qa", "version": "2"}}, 30)
        if "result" not in r:
            sys.exit(f"MCP server did not initialize: {r} (Studio open with MCP enabled? STUDIO_MCP_CMD set?)")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.tools = {t["name"]: t for t in self.req("tools/list", timeout=30).get("result", {}).get("tools", [])}
        self.builtin = "execute_luau" in self.tools or "list_roblox_studios" in self.tools \
            or any(k in " ".join(server_cmd()).lower() for k in ("studiomcp", "mcp.bat"))  # built-in lists no tools until a Studio connects
        self.studio_hint, self.studio_id = studio_hint, None
    def send(self, m):
        try: self.p.stdin.write(json.dumps(m) + "\n"); self.p.stdin.flush()
        except (BrokenPipeError, OSError): pass
    def req(self, method, params=None, timeout=60):
        self.n += 1; i = self.n
        m = {"jsonrpc": "2.0", "id": i, "method": method}
        if params is not None: m["params"] = params
        self.send(m); end = time.time() + timeout
        while time.time() < end:
            try: line = self.q.get(timeout=1)
            except queue.Empty:
                if self.p.poll() is not None: return {"error": f"server exited (see {TMP}/studio-mcp-stderr.log)"}
                continue
            try: r = json.loads(line)
            except ValueError: continue
            if r.get("id") == i: return r
        return {"error": f"timeout after {timeout}s"}
    def needs_studio_id(self, tool):
        props = self.tools.get(tool, {}).get("inputSchema", {}).get("properties", {})
        return "studio_id" in props
    def resolve_studio(self, wait_s=25):
        # built-in StudioMCP: every tool needs studio_id. Right after initialize the list is often still empty
        # (Studio reconnects to the server a few seconds later), so poll before giving up.
        if self.studio_id is None and "list_roblox_studios" in self.tools:
            end, txt = time.time() + wait_s, ""
            while self.studio_id is None:
                r = self.raw_call("list_roblox_studios", {}, 30)
                txt = json.dumps(r, ensure_ascii=False)
                items = r if isinstance(r, list) else (r.get("studios") or r.get("instances") or []) if isinstance(r, dict) else []
                for it in items:
                    if isinstance(it, dict):
                        sid = it.get("studio_id") or it.get("id") or it.get("studioId")
                        if sid and (not self.studio_hint or self.studio_hint.lower() in json.dumps(it, ensure_ascii=False).lower()):
                            self.studio_id = sid; break
                if self.studio_id is None:
                    if time.time() > end: break
                    time.sleep(2)
            if self.studio_id is None:
                print("list_roblox_studios (no match for --studio %r):" % self.studio_hint, txt[:1500])
            else:
                print("studio_id:", self.studio_id)
        return self.studio_id
    def raw_call(self, tool, args, timeout=120):
        r = self.req("tools/call", {"name": tool, "arguments": args}, timeout)
        if "result" not in r: return r
        parts = []
        for c in r["result"].get("content", []):
            if c.get("type") == "image":
                f = os.path.join(TMP, f"studio-mcp-{int(time.time()*1000)}.png")
                import base64; open(f, "wb").write(base64.b64decode(c.get("data", "")))
                parts.append(f"[image saved {f}]")
            else: parts.append(c.get("text", ""))
        txt = "\n".join(parts)
        try: return json.loads(txt)
        except ValueError: return {"text": txt, "isError": r["result"].get("isError", False)}
    def call(self, tool, args, timeout=120):
        args = dict(args)
        if self.needs_studio_id(tool) and "studio_id" not in args and tool != "list_roblox_studios":
            sid = self.resolve_studio()
            if sid: args["studio_id"] = sid
        return self.raw_call(tool, args, timeout)
    def luau(self, code, dm="Edit", timeout=120):
        if self.builtin: return self.call("execute_luau", {"code": code, "datamodel_type": dm}, timeout)
        if dm != "Edit": return {"error": "open-source server: only Edit via run_code; use play/run-pair"}
        return self.call("run_code", {"command": code}, timeout)
    def close(self):
        try: self.p.stdin.close(); self.p.terminate()
        except Exception: pass

INJECT = """local sps = game:GetService("StarterPlayer").StarterPlayerScripts
local old = sps:FindFirstChild(%(name)s) if old then old:Destroy() end
local s = Instance.new("LocalScript") s.Name = %(name)s s.Source = %(src)s s.Parent = sps
return "injected " .. s:GetFullName()"""
REMOVE = """local sps = game:GetService("StarterPlayer").StarterPlayerScripts
local s = sps:FindFirstChild(%(name)s) if s then s:Destroy() return "removed" end return "absent\""""

def lua_str(s):  # long-bracket string that cannot be closed by the content
    k = 0
    while ("]" + "=" * k + "]") in s: k += 1
    return "[" + "=" * k + "[" + s + "]" + "=" * k + "]"

def read(p): return open(p, encoding="utf-8").read()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd"); ap.add_argument("args", nargs="*")
    ap.add_argument("--timeout", type=int, default=120); ap.add_argument("--name", default="QA_Client")
    ap.add_argument("--out", default=os.path.join(TMP, "studio-mcp-last.json")); ap.add_argument("--json")
    ap.add_argument("--studio", help="pick the Studio whose list_roblox_studios entry contains this text")
    ap.add_argument("--run-tool", default=None); ap.add_argument("--play-tool", default="run_script_in_play_mode")
    a = ap.parse_args(); c = Client(a.studio); res = []
    try:
        if a.cmd == "tools":
            for t in c.tools.values(): print(f"{t['name']}: {t.get('description','')[:120]}")
            if a.json: json.dump(list(c.tools.values()), open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            print(f"server: {'built-in StudioMCP' if c.builtin else 'open-source rbx-studio-mcp'}")
            return
        run_edit = lambda code, t=60: (c.call(a.run_tool, {"command": code}, t) if a.run_tool else c.luau(code, "Edit", t))
        if a.cmd == "call": res.append(c.call(a.args[0], json.loads(a.args[1]) if len(a.args) > 1 else {}, a.timeout))
        elif a.cmd == "batch":
            for item in json.loads(read(a.args[0])):
                t0 = time.time()
                if isinstance(item, dict) and "sleep" in item: time.sleep(item["sleep"]); continue
                if isinstance(item, dict) and "luau" in item:
                    code = read(item["luau"])
                    for k, v in item.get("sub", {}).items(): code = code.replace(k, v)  # e.g. {"__N__": "2"}
                    dm, label = item.get("dm", "Edit"), f"luau {item['luau']} ({item.get('dm','Edit')})"
                    r = c.luau(code, dm, item.get("timeout", a.timeout))
                    # poll: repeat until the text contains item["until"] (e.g. a multiplayer test result in _G)
                    end = time.time() + item.get("max", 0)
                    while item.get("until") and item["until"] not in json.dumps(r, ensure_ascii=False) and time.time() < end:
                        time.sleep(item.get("every", 5)); r = c.luau(code, dm, item.get("timeout", a.timeout))
                else:
                    label, r = item[0], c.call(item[0], item[1] if len(item) > 1 else {}, item[2] if len(item) > 2 else a.timeout)
                print(f"== {label} ({time.time()-t0:.1f}s)"); print(json.dumps(r, ensure_ascii=False)[:6000]); sys.stdout.flush()
                res.append({"call": label, "result": r})
        elif a.cmd == "edit": res.append(run_edit(read(a.args[0]), a.timeout))
        elif a.cmd == "play":
            if c.builtin: sys.exit("built-in server has no run_script_in_play_mode: use batch with start_stop_play + execute_luau dm=Server")
            res.append(c.call(a.play_tool, {"code": read(a.args[0]), "mode": "start_play", "timeout": a.timeout}, a.timeout + 180))
        elif a.cmd == "inject-client":
            res.append(run_edit(INJECT % {"name": lua_str(a.name), "src": lua_str(read(a.args[0]))}))
        elif a.cmd == "remove-client": res.append(run_edit(REMOVE % {"name": lua_str(a.name)}))
        elif a.cmd == "run-pair":
            if c.builtin: sys.exit("built-in server: run the client probe directly with execute_luau dm=Client (batch)")
            res.append(run_edit(INJECT % {"name": lua_str(a.name), "src": lua_str(read(a.args[0]))}))
            try:
                res.append(c.call(a.play_tool, {"code": read(a.args[1]), "mode": "start_play", "timeout": a.timeout}, a.timeout + 180))
            finally:
                res.append(run_edit(REMOVE % {"name": lua_str(a.name)}))
        else: ap.error(f"unknown command {a.cmd}")
    finally:
        c.close()
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    bad = False
    for r in res:
        r = r.get("result", r) if isinstance(r, dict) and "call" in r else r
        if a.cmd != "batch":
            if isinstance(r, dict) and r.get("logs") is not None:
                print(f"success={r.get('success')} timeout={r.get('isTimeout')} value={str(r.get('value'))[:2000]} error={r.get('error')}")
                for l in r["logs"]:
                    if l.get("level") in ("warning", "error") or str(l.get("message", "")).startswith("[qa]"):
                        print(f"  [{l.get('level')}] {str(l.get('message'))[:600]}")
            else: print(json.dumps(r, ensure_ascii=False)[:3000])
        bad = bad or (isinstance(r, dict) and bool(r.get("error") or r.get("isError") or r.get("success") is False))
    print(f"(saved {a.out})"); sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
