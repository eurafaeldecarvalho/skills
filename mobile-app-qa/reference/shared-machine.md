# Shared machine etiquette and resource reservation (mandatory step 0)

Often several agents share ONE machine: same CPU, RAM, disk, `/home`, and the same Android SDK. An emulator
(2–4 GB), a Gradle release build (3–6 GB plus daemons) and Maestro/Java can starve each other, freeze the box
or kill another agent's run. Real incident: one agent overwrote the shared `cmdline-tools` while another was
using them. So **before any build, emulator, Maestro run, matrix sweep, red-team chaos or FINAL PASS**:

## 1. Look before you start
```bash
nproc; free -h; uptime; df -h /home
ps -eo pid,user,etimes,rss,comm --sort=-rss | grep -E 'qemu|emulator|gradle|java|node|maestro' | grep -v grep
adb devices                                   # emulators already running (whose?)
scripts/box-reserve.sh status                 # all of the above + live locks + booked slots
```
If RAM available < ~6 GB or another emulator/build is running, you are not alone — don't start anything heavy.

## 2. Book a slot (shared schedule + lock files)
- Schedule: `/home/box/shared/box-schedule.md` (markdown table; box-local time, BRT on the owner's box).
  Locks: `/home/box/shared/locks/<resource>.lock` (`project`, `owner`, `start`, `end`, `pid`, `host`).
- Resources: `build`, `emulator` (book both for build + QA), or `all` for exclusive use. Recurring rows are
  allowed (`| daily 09:00 | 12:00 | … | recurring from YYYY-MM-DD |`).
```bash
export BOX_PROJECT=EvenKeel
scripts/box-reserve.sh reserve -p "$BOX_PROJECT" -o "<agent>" -r build,emulator \
  -s "2026-10-30 17:00" -e "2026-10-30 21:00" -n "release build + FINAL PASS"
```
- Exit 3 = overlap: **message the other agent(s)** with the proposed slot and wait for an explicit OK; then book
  (`--force` only with that OK, noted in `-n`). No answer = pick a free slot. Honor other agents' slots, even if
  their machine looks idle.
- The owner can set fixed slots for agents (e.g. one project's emulator QA every evening); treat them as booked.

## 3. Hold the lock while you run — and always release
```bash
scripts/box-reserve.sh acquire -p "$BOX_PROJECT" -r build,emulator --pid $$ \
  && trap 'scripts/final-pass.sh stop; (cd android && ./gradlew --stop); scripts/box-reserve.sh release -p "$BOX_PROJECT" -r build,emulator' EXIT
```
`acquire` refuses outside your slot (exit 4), while someone else holds a live lock (exit 4) or when free RAM is
below `MIN_FREE_GB` (exit 5). `final-pass.sh` and `matrix-sweep.sh` refuse to start without a valid lock
(`BOX_FORCE=1`/`--force` only when the owner said the box is yours). Release on success **and** failure.

## 4. Resource caps (stay a good neighbour)
| Thing | Cap |
|---|---|
| Emulators | **one per agent**; `-memory 4096 -cores 4` max; `-no-window -gpu swiftshader_indirect`; started via `nice -n 10 ionice -c2 -n7` |
| Gradle | `org.gradle.jvmargs=-Xmx3g` (project `gradle.properties` or `-Dorg.gradle.jvmargs=-Xmx3g`), `--max-workers=2`, `nice`; `./gradlew --stop` after |
| Metro/Node/Jest | `--maxWorkers=2`; stop dev servers you started |
| Disk | build outputs and screenshots inside your project; delete your own temp APKs/videos after the report |
| Cleanup | `adb -s <your serial> emu kill`, `./gradlew --stop`, kill only PIDs you started (recorded in your pid files) |

**Never kill, renice or `adb emu kill` another agent's processes/emulators**, even if they look stuck — message
the owner agent or the user.

## 5. Shared Android SDK: add-only
- Only **add** packages (`sdkmanager "<pkg>"`). Never `--uninstall`, never delete/overwrite/move
  `cmdline-tools`, `platform-tools`, `emulator` or `build-tools` others use; never re-extract a cmdline-tools zip
  over `cmdline-tools/latest`. Need a different version? Install side by side (`cmdline-tools;<ver>`).
- Namespace your stuff: AVDs `<project>-<name>` (`final-pass.sh` uses `AVD_PREFIX`, default = project slug),
  emulator ports chosen to not collide (check `adb devices`), files under your project dir.
- Licence prompts/updates that change shared components: ask the owner first.

## 6. When the slot ends before the loop does
- Check time left (`box-reserve.sh left -p … -r emulator`) before each heavy phase; don't start a phase you
  can't finish (a FINAL PASS profile ≈ 45–90 min).
- Pause cleanly: finish the current step, write the ledger/state (`qa/STATE.md`: iteration, phase, next config,
  seeds), stop your emulator and Gradle, release the lock. `matrix-sweep.sh` stops itself (exit 75) when fewer
  than `MIN_LEFT` minutes remain and resumes with the same `OUT` (finished configs are skipped).
- Book the next slot and resume there. A paused iteration is **incomplete**: it never counts as a clean
  iteration until all its phases ran (see [convergence-loop.md](convergence-loop.md)).
