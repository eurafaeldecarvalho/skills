---
name: game-taste-3d
description: >-
  Make a stylized/low-poly 3D game LOOK beautiful and intentional instead of cheap, generic, or
  "asset-flip" — the art-direction layer for light, clean 3D (think PEAK, A Short Hike, Monument Valley,
  Sable; NOT AAA realism). Use whenever designing, generating, choosing, or reviewing a 3D game's
  visuals: palette and color, lighting and post-processing, materials/shaders (flat, toon/cel, vertex
  colors, matcap), silhouette and modeling, 3D camera (FOV, follow, shake), characters/mascots, or the
  asset/engine pipeline for web/Steam; when a 3D scene looks flat, muddy, plasticky, "Unity-default",
  asset-flippy, or AI-slop; and when deciding how to make low-poly look premium while staying light.
  Reach for it even when the user just says "it looks cheap" about a 3D game. The 3D counterpart of
  `game-taste-2d`; pairs with `game-feel` (motion/juice) and `game-polish` (the audit pass).
---

# Game taste — 3D (art direction for stylized/low-poly 3D)

**The one thesis:** in stylized 3D, beauty comes from **art direction — restricted palette + authored
light + silhouette + consistency — not from polygons or PBR.** And the same choices that look premium
(one shared material, one palette, flat/baked shading) are also what make it run fast. A low-poly scene
looks cheap because of mixed densities, default shaders, and no lighting — never because it has few
polygons. This skill is for light 3D shipping to the web and/or Steam, built by a solo dev + AI.

Siblings: **`game-feel`** (how it feels — easing, shake, hit-stop, SFX) and **`game-polish`** (the
whole-build audit). This skill is how the 3D game LOOKS. What transfers unchanged from `game-taste-2d`:
palette discipline, reserving one accent for focus, composition/hierarchy, the thumbnail test, the
color-script idea, and the anti-slop instinct.

## The one rule: lock constraints BEFORE modeling
Lock **one camera, one palette, one shading model** on day one. Restraint is the feature: Monument
Valley's team discarded 70–90% of their work to keep the look clean; Journey chose stylization because
realism "is so hard to achieve" and ages badly. For a solo dev + AI it's the only sustainable path.

## 1. Palette & cohesion
- **<15 colors**, 5 families (shadow / mid / light / accent / white), **one accent reserved only for the
  player/interactive/focus** (Journey's hero red is "never lost in the environment"). **Sample the
  palette from a real photo**, never eyeball hex.
- **One shared palette texture + one material for (almost) the whole game:** a tiny grid of flat colors
  UV-mapped onto every model. Recoloring = editing one image, discipline is enforced by the pipeline,
  and everything batches into few draw calls. This is the #1 cheap-cohesion trick — and it's performance,
  not just taste.
- **Color as script:** plan how the palette shifts across the experience to guide emotion (Journey:
  warm → deep blue → near-colorless). Judge it as a whole — make a contact sheet of screenshots.

## 2. Silhouette first, density consistent
- **Model the black-fill silhouette before any interior detail, and exaggerate it** — "timid geometry
  reads as unfinished rather than stylized." One dominant shape language per object (bean, blob,
  tall-thin, short-stubby).
- **Thumbnail test (the readability gate):** judge the scene at ~231px wide and zoom screenshots out as
  you work. Strong silhouette + high value contrast + ONE focal point must survive shrinking.
- **Faceting/triangle budget per asset class and hold it.** A 300-tri tree next to a 30,000-tri rock
  breaks the world — mixed density is the #1 asset-flip tell. Rough budgets: hero/characters 1k–5k tris;
  props/foliage a few hundred.

## 3. Shading model (pick one and stay there — never PBR)
- **Flat/faceted shading must be VISIBLE on low geometry** (`flatShading: true`, per-face normals).
  Smoothing groups over low poly = "cheap mobile-game look." Rule of thumb: **3 values per material,
  warm light / cool shadow.**
- **Vertex colors are the web default**, not textures: color painted into vertices = zero UVs, zero
  texture downloads, runs anywhere. Move to a texture only when flat color truly can't carry it.
- **Toon banding** via `MeshToonMaterial` + a gradient ramp kept `NearestFilter` (hard bands); start at
  2–3 steps. Near-Lambert cost, far cheaper than PBR.
- **`MeshMatcap` = light baked into a texture, near-zero cost** — great for static props with a stable
  camera (but the light locks to the camera, so not for a hero needing directional cues).
- The **cel look is 3 independent dials**, mix per readability: (1) outline, (2) light banding, (3) flat
  color/texture. (Borderlands = outline+banding; TF2 = flat texture, no outline; Wind Waker = flat+banding.)
- **Never PBR** for this target (metal/rough/normal/env). Default grey Principled BSDF / plastic Phong on
  everything is the death of identity.

## 4. Lighting & atmosphere (the "premium" lever)
- **Core light recipe:** one strong key `DirectionalLight` (the sun, ~45°, the ONLY shadow caster) + a
  cheap `HemisphereLight` fill (0.2–0.3, sky-tint up / ground-tint down = free volume, no shadow) +
  **colored ambient and colored shadows** (warm light / cool shadow). Cap the scene at **2–4 lights**,
  shadow only on the sun.
- **BAKE everything static** (the rule that makes low-poly look expensive while staying cheap): light +
  AO + bounce baked in Blender to a lightmap/vertex colors, displayed unlit or as lightMap/aoMap. Runtime
  goes nearly idle.
- **Fog is the cheapest depth + mood trick — never ship web 3D without it.** `scene.fog` (FogExp2
  ~0.01–0.03). Its color MUST equal the sky/horizon color, or you get a visible "wall" of fog. Lets you
  shorten the far plane for free FPS and hides pop-in.
- **Stylized ambience kit = gradient skybox + fog + hemisphere, all sharing ONE horizon color** (cheap
  unlit gradient sky, not a multi-MB HDRI).
- **Tonemapping is a flavor choice — test it, don't default to ACES** (it desaturates/hue-shifts and
  washes flat colors). Try `NeutralToneMapping` or `NoToneMapping` first, exposure ~1.0; set
  `outputColorSpace = SRGBColorSpace`.
- **AO / contact shadows ground objects** — floating objects read as broken; subtle blob/baked AO under
  everything. **Rim/Fresnel only on hero/enemies** to pop them off the background, never the whole scene.
- **Post-processing last and subtle, one effect at a time.** Bloom: threshold high (~0.85), strength
  0.4–0.8, prefer selective/emissive-only. Subtle vignette. **Skip real DoF on the web** (fake depth with
  fog + vignette). Each fullscreen pass costs on mobile.

## 5. Camera
- **Follow via SmoothDamp** (spring-damper, no overshoot), smoothTime 0.15–0.25s, offset ~(0, 3, −6).
  Gotchas: velocity must be a **class field** (a local resets every frame → camera jams); call it
  **after** physics (LateUpdate); don't multiply by dt (it's internal).
- **FOV 55–65** for third person (start ~58). 85–100 "for epicness" = distortion + motion sickness
  (anti-slop). Juice: widen +5–10 on sprint via SmoothDamp, ease back.
- **Shake by TRAUMA** (Eiserloh, GDC 2016): trauma 0..1, events add, decay ~1–1.5/s, shake = trauma²·max,
  driven by **Perlin/simplex noise with different seeds per axis** (random-per-frame = buzzy jitter).
- **Punch ≠ shake** — a short directional spring-back impulse (recoil/dash), implemented separately.
  Trauma = ambient chaos; punch = single-event feedback. (Shake/punch tuning details → `game-feel`.)
- **Lock the camera when you can** (fixed iso/angle, like Monument Valley) — removes most composition and
  occlusion problems; the easiest web win. Depth cue = fog + light vignette.

## 6. Character & modeling
- **Silhouette is the load-bearing decision** — design it first as a solid black shape; if it isn't
  recognizable as a black blob at ~48px, it fails. Meme-ability (Among Us bean, Fall Guys jellybean) =
  ONE dominant shape + exaggerated proportions, never added geometry.
- **One fidelity across the whole cast** (never realistic PBR on a low-poly mesh); one proportion system.
- **Color with flat vertex colors / one shared palette-strip + a 2-tone toon ramp.** Customization is
  cheap: swap colors/cosmetics on ONE base mesh (PEAK's charm) rather than modeling variants.
- **Blender pipeline that stays light by construction:** silhouette base mesh → add geometry only where
  the form needs it → Decimate → keep clothing close to the body → assign palette at UV → rig with Rigify;
  do the toon look with shader nodes, not an add-on.
- **Cheapest rig/anim:** Mixamo auto-rigs a humanoid in ~2 min with a free locomotion library; it has no
  facial blend shapes, so hand-make a few in Blender. Layer procedural code on top (IK foot-plant, look-at,
  idle breathing, squash/stretch). **Non-humanoid mascots → no-rig** (scale squash/stretch, 2-bone bend,
  TABS-style procedural wobble).

## 7. Performance (cohesion trick = performance trick)
- **Draw calls matter more than triangles** — most slow three.js scenes are draw-call-bound. Keep draw
  calls ~<100–150. Share ONE master material; `InstancedMesh` for repeats (1000 trees = 1 draw call);
  merge static geo (`mergeGeometries`); verify with `renderer.info`. (Atlasing alone does NOT cut draw
  calls if you keep per-object material slots.)
- **glTF optimize in a fixed order** (compression is lossy → last; keep uncompressed originals):
  resize/compress textures → quantize (`KHR_mesh_quantization`) → Draco (static) or meshopt (skinned) →
  simplify → prune/dedupe. Start: `gltf-transform optimize in.glb out.glb --texture-compress webp`, then
  Brotli/gzip. **Textures are 80%+ of file size** (WebP for one model, KTX2/Basis for sets). Compression
  shrinks downloads, it does NOT speed rendering — bake lighting so you ship almost no runtime lights.

## 8. Engine & asset pipeline
- **Build web-first on three.js via react-three-fiber + drei.** Lightest runtime (three core
  ~168kB min+gzip, no multi-MB wasm cold start), largest LLM training corpus (AI writes it reliably), and
  the declarative JSX keeps AI-generated errors localized. Babylon.js only if you want batteries-included
  TS + native WebGPU.
- **Avoid Unity/Godot for the WEB** (empty Unity 6 WebGL ~8–11MB Brotli; Godot 4 web wasm ~4–12MB that
  must download *and* compile before first paint — kills virality). For Steam, wrap the web build in Tauri,
  or go Godot native only if the game pivots to Steam-first.
- **AI is great at scene CODE, poor at production MESHES.** AI meshes (Tripo/Meshy) are **blockouts only**
  — raw output has messy triangulation + muddy textures (the AI-slop tell). Pipeline: AI generate → Blender
  decimate/retopo → recolor to the flat palette → Mixamo rig. A tight hand-made/kitbashed kit (Kenney CC0,
  Synty, Quaternius) usually beats fighting genAI topology.
- **Steam AI disclosure (Jan 2026):** AI-written *code* needs no disclosure; AI-generated art/audio/
  text/VO that ships must be disclosed on the store page. Keep generation logs.

## Anti-slop checklist (run as a final gate)
- Engine-default scene (untouched Standard/Principled + default skybox + 1 light + zero post) = the #1
  asset-flip signal.
- Smooth-shaded low poly; realistic/photo PBR on low poly; inconsistent polygon density between assets.
- No palette discipline (too many colors, no families, no reserved accent); default #808080 grey material.
- Shipping raw AI mesh (messy topo + muddy bake); texturing what vertex-color+ramp already solves.
- No fog / fog color ≠ sky; no AO/contact shadow (floating objects); everything lit flat with no
  warm-light/cool-shadow separation.
- Over-stacked post (strong bloom + ACES + chromatic aberration + DoF = washed, blurry, slow). Start at
  ZERO post, add one at a time; low-threshold bloom = milky haze.
- FOV 85–100 "for epic"; real DoF on the web; random-per-frame shake; SmoothDamp velocity as a local.
- Timid silhouette; over-detailed faces/fingers; inconsistent shape language; not testing at thumbnail size.

## How to apply (build or review)
1. Lock palette (sampled from a photo) + one material + one camera + one shading model. Day one.
2. Silhouette-first modeling; run the thumbnail/48px black-blob test on hero and scene.
3. Set the light recipe (sun + hemisphere, warm/cool), add fog = sky color, bake statics.
4. Choose and hold the shading dial(s); keep vertex-color/toon; never PBR.
5. Tune camera (SmoothDamp follow, FOV ~58, trauma shake, lock if possible).
6. Optimize: one master material, instancing, bake, glTF compress last. Verify draw calls.
7. Add post last, one effect at a time; test tonemapping (not auto-ACES).

## Reference games
PEAK (north star: bright toon, readable traversal, cheap customization) · A Short Hike (render-to-low-res
crunch + photo-sampled palette) · Monument Valley (fixed iso, <15 colors, radical restraint) · Sable
(cel + Moebius ink outlines via post edge-detection) · Untitled Goose Game (flat-shaded, untextured) ·
Journey (HDR color guiding emotion, reserved hero accent, distant focal mountain) · Among Us / Fall Guys
(meme silhouettes) · Islanders / Townscaper (clean minimal low-poly) · Firewatch (color grade + fog
vistas) · Bruno Simon's portfolio (fast, premium three.js web 3D).
