# FINAL PASS — prove the build that players will get

The convergence loop runs on a local build. The FINAL PASS runs once on the artifact players will actually
receive, after the loop exits, and repeats if it finds anything (that finding reopens the loop).

1. **Clean build:** fresh clone at the release commit → `verify.sh` with `STATIC=required FLAKE=3` → `rojo build`.
   Record the commit sha. Studio must not hold edits that aren't in git (diff the place if in doubt).
2. **Publish to a non-public target first**, with the owner's approval: the existing place with private/playtest
   access, or a test place of the same universe. Never "Publish as new" by accident. Record the place version.
3. **Real servers, not Studio:** join the published place (box client inside a booked slot, and a real device).
   Export F9 / Output and run `output-scan.py` on it; confirm `game.PlaceVersion` matches the recorded version.
4. **Update path:** data written by the previous published version still loads (keep a test account/profile from
   the old version, or a fake-server test with an old-schema record); a schema change has a migration and a test.
   Decide whether running servers need "Migrate to latest update" / shutdown, and note the impact on live players.
5. **Real devices and people:** the weakest target phone plays one full loop (touch, landscape, dimmest scene);
   2 real players play the loop together; console/TV if targeted. If people or devices aren't available now,
   mark Blocked and hand an **operator script** (numbered steps, expected result per step, what to write down).
6. **Rollback rehearsal:** note the previous place version and how to restore it (version history) before going public.
7. Only then switch access to the public audience (owner decision) and re-check F9 on the first live server.

Evidence for each step goes to `qa/<date>/final/` and the FINAL PASS table of the report.
