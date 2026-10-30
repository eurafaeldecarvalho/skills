#!/usr/bin/env python3
"""studio-mcp.py — minimal stdio client for a Roblox Studio MCP server (built-in StudioMCP or the
open-source rbx-studio-mcp). Lets a QA script drive Studio without an agent UI.

  studio-mcp.py tools                               list the server's tools
  studio-mcp.py call TOOL '{"json":"args"}'         call any tool
  studio-mcp.py edit FILE.luau                       run Luau in EDIT mode (run_code)
  studio-mcp.py play FILE.luau [--timeout 120]       run Luau on the SERVER of a play session (run_script_in_play_mode,
                                                     mode start_play; Studio returns to edit mode afterwards)
  studio-mcp.py inject-client FILE.luau [--name QA_Client]   add FILE as a LocalScript in StarterPlayerScripts (edit mode)
  studio-mcp.py remove-client [--name QA_Client]     remove it again (ALWAYS do this before saving/publishing)
  studio-mcp.py run-pair CLIENT.luau SERVER.luau [--timeout 120]   inject → play SERVER → remove (even on failure)

Client code can't be run directly by the play tool (it runs on the server), so client probes such as
ui-audit.client.luau report back through a RemoteEvent that the server script (qa-collect.server.luau) prints.
Every result is printed and saved as JSON with --out (default /tmp/studio-mcp-last.json) for output-scan.py.
Env: STUDIO_MCP_CMD = the server command (default: rbx-studio-mcp --stdio on PATH). Tool names differ
between server builds: run `tools` first and override with --run-tool / --play-tool if needed.
Shared machine: Studio is a heavy job — book it with box-reserve.sh and pass box-preflight.sh first.
"""
import argparse, json, os, queue, shlex, subprocess, sys, threading, time

def open_server():
    cmd = shlex.split(os.environ.get("STUDIO_MCP_CMD", "rbx-studio-mcp --stdio"))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=open("/tmp/studio-mcp-stderr.log", "a"), text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()
    return p, q

class Client:
    def __init__(self):
        self.p, self.q = open_server(); self.n = 0
        r = self.req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                    "clientInfo": {"name": "roblox-game-qa", "version": "1"}}, 30)
        if "result" not in r:
            sys.exit(f"MCP server did not initialize: {r} (is Studio open with MCP enabled? STUDIO_MCP_CMD set?)")
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    def send(self, m):
        try: self.p.stdin.write(json.dumps(m) + "\n"); self.p.stdin.flush()
        except BrokenPipeError: pass
    def req(self, method, params=None, timeout=60):
        self.n += 1; i = self.n
        m = {"jsonrpc": "2.0", "id": i, "method": method}
        if params is not None: m["params"] = params
        self.send(m); end = time.time() + timeout
        while time.time() < end:
            try: line = self.q.get(timeout=1)
            except queue.Empty:
                if self.p.poll() is not None: return {"error": "server exited (see /tmp/studio-mcp-stderr.log)"}
                continue
            try: r = json.loads(line)
            except ValueError: continue
            if r.get("id") == i: return r
        return {"error": f"timeout after {timeout}s"}
    def call(self, tool, args, timeout=120):
        r = self.req("tools/call", {"name": tool, "arguments": args}, timeout)
        if "result" not in r: return r
        txt = "\n".join(c.get("text", "") for c in r["result"].get("content", []))
        try: return json.loads(txt)
        except ValueError: return {"text": txt, "isError": r["result"].get("isError", False)}
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

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd"); ap.add_argument("args", nargs="*")
    ap.add_argument("--timeout", type=int, default=120); ap.add_argument("--name", default="QA_Client")
    ap.add_argument("--out", default="/tmp/studio-mcp-last.json")
    ap.add_argument("--run-tool", default="run_code"); ap.add_argument("--play-tool", default="run_script_in_play_mode")
    a = ap.parse_args(); c = Client(); res = []
    try:
        if a.cmd == "tools":
            r = c.req("tools/list", timeout=30)
            for t in r.get("result", {}).get("tools", []): print(f"{t['name']}: {t.get('description','')[:100]}")
            return
        if a.cmd == "call": res.append(c.call(a.args[0], json.loads(a.args[1]) if len(a.args) > 1 else {}, a.timeout))
        elif a.cmd == "edit": res.append(c.call(a.run_tool, {"command": open(a.args[0]).read()}, a.timeout))
        elif a.cmd == "play":
            res.append(c.call(a.play_tool, {"code": open(a.args[0]).read(), "mode": "start_play", "timeout": a.timeout}, a.timeout + 180))
        elif a.cmd == "inject-client":
            res.append(c.call(a.run_tool, {"command": INJECT % {"name": lua_str(a.name), "src": lua_str(open(a.args[0]).read())}}, 60))
        elif a.cmd == "remove-client": res.append(c.call(a.run_tool, {"command": REMOVE % {"name": lua_str(a.name)}}, 60))
        elif a.cmd == "run-pair":
            res.append(c.call(a.run_tool, {"command": INJECT % {"name": lua_str(a.name), "src": lua_str(open(a.args[0]).read())}}, 60))
            try:
                res.append(c.call(a.play_tool, {"code": open(a.args[1]).read(), "mode": "start_play", "timeout": a.timeout}, a.timeout + 180))
            finally:
                res.append(c.call(a.run_tool, {"command": REMOVE % {"name": lua_str(a.name)}}, 60))
        else: ap.error(f"unknown command {a.cmd}")
    finally:
        c.close()
    json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False)
    bad = False
    for r in res:
        if isinstance(r, dict) and r.get("logs") is not None:
            print(f"success={r.get('success')} timeout={r.get('isTimeout')} value={str(r.get('value'))[:2000]} error={r.get('error')}")
            for l in r["logs"]:
                if l.get("level") in ("warning", "error") or str(l.get("message", "")).startswith("[qa]"):
                    print(f"  [{l.get('level')}] {str(l.get('message'))[:600]}")
        else: print(json.dumps(r, ensure_ascii=False)[:3000])
        bad = bad or (isinstance(r, dict) and (r.get("error") or r.get("isError") or r.get("success") is False))
    print(f"(saved {a.out})"); sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
