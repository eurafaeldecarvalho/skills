# Case study — "Turno da Madrugada" (2-player co-op horror, Rojo + Luau, pt-BR/en)

A real run of this skill on a shared box without GPU (~9 GB free RAM, no swap), Studio under Wine, Studio driven by
an agent through Studio MCP. Project-specific names below are examples, not rules.

## What worked
- **Headless first, Studio last.** `verify.sh`-style chain (luau-compile → rojo build → luau-lsp analyze with
  Roblox definitions → selene → stylua → debug-flag grep → Lune) caught 22 type errors and a dead branch before
  anyone opened Studio. 353 Lune tests ran in seconds and twice per iteration (flake check).
- **Fake server in Lune** (`tests/servidor_falso.luau`): runs the REAL server scripts (Main + services) on a fake
  DataModel with a virtual clock, fake Players and fake remotes; only visual/platform services are stubbed. With it,
  `dupla.spec` (16 cases) covered two players, partner leaving mid-shift → solo, late joiner taking the free post,
  kick, spectator and the countdown waiting for the partner — things a 1-client box can't run in Studio.
  Mutation check: deliberately breaking the server made the spec fail (proves the test sees the real code).
- **Pure layout math** (`escala.spec`): the UI scale and positions computed for 13 screens × 6 contexts (phone
  portrait/landscape, tablet, desktop, console) — catches overlap and tiny text without rendering.
- **Instance counts per round** as the leak oracle: the server returned to the same instance count (game and
  workspace) after rounds 1 and 3.
- **Studio MCP play** with a temporary client LocalScript (injected, then removed, place never saved) reported UI
  facts back to the server; a rate-limit fix was confirmed live (53 → 4 accepted requests).
- **Memory log** during Studio runs, and an operator script for what the box can't do (Device Emulator presets, 2
  real clients, real phone).

## What went wrong (and became rules in this skill)
- A 2-client "Clients and Servers" run didn't fit in RAM next to another agent's emulator → shared-box booking +
  RAM pre-flight; items needing it are Blocked, not passed (shared-box.md).
- Text measured at 9.9 px on an iPhone SE-sized viewport passed visual review → numeric text floor + ui-audit.
- The open cloud place in Studio didn't contain the latest local commits, so a smoke test would have tested old code
  → FINAL PASS builds from a clean commit and checks the place version (final-pass.md).
- The last batch of fixes was made headless and never re-verified in a real play session; the report still scored
  from the earlier pass → convergence loop (re-run the whole pass, two clean iterations).
- Spam on two remotes was only noticed live → red-team rows every iteration (red-team.md).
- The end-of-round screen only left on a button press (fixed with an automatic advance) → "every overlay has an
  automatic exit" became a FEATURES.md cross-cutting row.
