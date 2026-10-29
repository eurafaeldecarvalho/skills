# Visual, audio & performance (dimensions 7-8)

## Lighting & readability
- Check every scene on a phone at mid brightness. Night/indoor scenes: raise `Ambient`/`OutdoorAmbient`,
  use `ExposureCompensation`, local `PointLight`/`SurfaceLight` on play areas, Atmosphere for depth.
  "Moody" that hides the stations is a P1.
- Lighting technology chosen for the target devices (Future looks best but costs more on low-end).
- Important signals (order ready, time low, danger) use shape + motion + sound, not color only.
- Art direction and juice: run `game-taste-3d` and `game-feel` for this layer.

## Assets
- Output/F9 must show no "failed to load"/"asset not found"/permission errors on server or client.
- Audio, animations, meshes and decals must be owned by or permitted for this experience/group
  (shared via asset privacy); assets that work for the owner in Studio may fail for players.
- Use `ContentProvider:PreloadAsync` for first-screen assets; no grey boxes on first spawn.
- NPC rigs: correct R6/R15, `HumanoidRootPart` anchored for static NPCs, animations through
  `Animator:LoadAnimation`, priorities set, no T-pose, no floating or sinking.

## Audio
- Every core action and state change has a sound; music optional but intended.
- Route sounds through `SoundGroup`s (Music/SFX/UI) with a settings mute; normalize volumes, no spikes
  louder than the music; 3D sounds have sensible roll-off.
- Music loops cleanly; nothing loud plays on join.

## Performance budgets (set real numbers in GAME.md)
- Test on the weakest target phone during the busiest moment (full server, most effects).
- Developer Console (F9): Memory (client and server), Script performance, Network.
- MicroProfiler: look for long frames, heavy scripts, physics spikes, render costs.
- Instances: anchor static parts; turn off `CanCollide`/`CanTouch`/`CanQuery` where unused; use
  `CollisionFidelity = Box/Hull` for decorative meshes; merge tiny parts; limit lights and particles.
- Streaming for large maps (`StreamingEnabled`, sensible `StreamingTargetRadius`).
- Scripts: no busy `while true do` without `task.wait`, no per-frame `Instance.new`, pool effects,
  disconnect per-round connections, no unbounded tables that grow every round.

## Anti-patterns
- Judging darkness on a bright desktop monitor.
- Using marketplace audio that isn't permitted for the experience.
- Profiling only an empty server.
