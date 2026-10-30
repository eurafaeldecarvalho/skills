# Build & release config (dimension 1)

Goal: what testers and the store get is the same thing you tested, built from a clean checkout.

## Test the release build, never only Expo Go / dev client
Release-only bugs: Hermes bytecode differences, minification/R8 stripping native classes, missing env
vars (`EXPO_PUBLIC_*` inlined at build time), `__DEV__` branches, dev-only polyfills, LogBox hiding
errors, Fast Refresh masking stale state, and config plugins that only apply at prebuild.
```bash
npx expo-doctor                       # dependency/SDK mismatches
npx tsc --noEmit && npx eslint . && npm test
npx expo config --type public | less  # final resolved app config (plugins, userInterfaceStyle, scheme, versions)
npx expo prebuild --clean --platform android   # in a throwaway copy if the repo uses CNG
# local release build (heavy; respect box reservations) or EAS:
cd android && ./gradlew assembleRelease   # or bundleRelease → bundletool for an installable APK
eas build -p android --profile preview    # cloud alternative (check plan limits)
```
AAB → APK for the emulator:
`bundletool build-apks --bundle app.aab --output app.apks --mode universal && unzip -p app.apks universal.apk > app.apk`.

## Config checklist
- [ ] `app.json`/`app.config.*`: `version` + `android.versionCode` bumped; `package` final; `scheme` set
      for deep links; `userInterfaceStyle` + **`expo-system-ui` installed** if it should follow the system.
- [ ] Every config plugin needed at runtime listed in `plugins` (splash dark config, notifications icon/color,
      localization `supportsRTL`, build-properties).
- [ ] Permissions in the merged manifest are only those used (`aapt dump permissions app.apk`); remove
      leftovers (e.g. RECORD_AUDIO from an unused library) — Play policy and user trust.
- [ ] `targetSdkVersion` meets the current Play requirement; edge-to-edge behaviour reviewed for it.
- [ ] Env: production keys only in EAS secrets/env; nothing secret in `EXPO_PUBLIC_*`; no `.env` or
      `google-services.json` with private keys committed in public repos (the Firebase client file is
      not a secret but restrict its API key).
- [ ] Error reporting (Sentry/Crashlytics) works in release with source maps uploaded.
- [ ] OTA (expo-updates): `runtimeVersion` policy correct; an update never ships native changes; test
      update download + rollback on a real release build.
- [ ] App size reasonable; ProGuard/R8 rules for native libs if minify enabled.
- [ ] Debug menus, test accounts and verbose logging compiled out; logs contain no PII/tokens.

## Anti-patterns
- "Works in Expo Go" as evidence. · Testing a dev build with Metro and calling it release QA. ·
  Changing `app.json` and expecting it without a rebuild. · Building from a dirty tree.
