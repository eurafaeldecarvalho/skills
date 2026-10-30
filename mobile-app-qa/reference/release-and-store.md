# Release & store (dimension 10)

## Tracks and the free pre-launch report
- Internal testing (up to 100 testers, fast) → closed testing → open → production. New personal developer
  accounts must run a closed test with enough opted-in testers for the required period before production
  (check current Play Console rules).
- **Pre-launch report**: Play runs your app automatically on real devices (crawler + screenshots +
  crash/ANR, accessibility, security, performance warnings) for builds on closed/open tracks (and internal
  if enabled). Free. Give it a test login (Play Console → Testing → Pre-launch report settings) and
  robo-script/deep links so it gets past sign-in. Review every screenshot: it shows other locales/devices.
- **Firebase Test Lab** (Spark/free: ~10 virtual + 5 physical test runs per day; check quotas) for robo or
  instrumentation tests on device models you don't own. Note: Google announced Test Lab's deprecation
  (shutdown 2027-09-30) — don't build long-term CI on it.
- Measured results for these and other device clouds (what worked, quotas, gotchas):
  [device-clouds.md](device-clouds.md).
- Store-installed smoke test: after rollout to a track, install from Play on a real phone and run the
  core flow (Play signing, App Bundle splits and dynamic delivery can differ from your local APK).

## Listing & compliance
- Data safety form matches actual collection (incl. SDKs: analytics, crash, auth providers).
- Account deletion: in-app path **and** a web URL in the listing.
- Privacy policy URL live and localized; content rating; target audience (children/families rules if
  relevant); permission declarations (e.g. photo/video permissions policy).
- Listing localized per market (title, short/full description, screenshots captured from the sweep in
  that locale and theme) — consistent with the in-app glossary.
- Staged rollout with crash/ANR monitoring; halt criteria written before rollout.
