# Sources and credits

## Method
- **Impeccable** by Paul Bakaus (Apache-2.0) — audit/critique/harden/polish passes, 0–4 scores, P0–P3,
  "detector output is evidence, not proof", screenshots from the real runtime. This skill adapts the
  method to mobile apps; no text copied. <https://github.com/pbakaus/impeccable>

## Similar skills found (2026-10) — and what this one adds
- simiancraft `android-emulator-harness` (headless AVD + Maestro on Linux/KVM):
  <https://github.com/simiancraft/simiancraft-skills/blob/main/skills/android-emulator-harness/SKILL.md>
- Callstack agent-skills (react-native-testing, agent-device, dogfood exploratory QA):
  <https://github.com/callstackincubator/agent-skills>
- eagleisbatman `maestro-testing`: <https://github.com/eagleisbatman/maestro-skill>
- johnkozaris `mobile-flows-maestro`:
  <https://github.com/johnkozaris/jko-claude-plugins/blob/main/plugins/maestro-mobile-validator/skills/mobile-flows-maestro/SKILL.md>
- AndyChangTW maestro native testing skill: <https://github.com/AndyChangTW/maestro-native-mobile-testing-skill>
- PramodDutta qaskills `maestro-mobile`: <https://github.com/PramodDutta/qaskills>
- elihuvillaraus `tester-mobile` (Expo/RN static + Jest + Maestro):
  <https://github.com/elihuvillaraus/skills/commit/f0b4b68a18b3e6412591c68ef873528306d87bc7>
- majiayu000 claude-skill-registry (component-testing-mobile, maestro-testing):
  <https://github.com/majiayu000/claude-skill-registry>
Gap they leave: none combines a feature inventory + functional E2E + a theme × locale × font × size
screenshot matrix + locale conventions + translation quality + a severity/score release gate + a
fix-until-green loop.

## Platform docs
- Expo color themes / `userInterfaceStyle` + expo-system-ui: <https://docs.expo.dev/develop/user-interface/color-themes/>
- Expo edge-to-edge (SDK 54): <https://expo.dev/blog/edge-to-edge-display-now-streamlined-for-android>
- expo-localization: <https://docs.expo.dev/versions/latest/sdk/localization/>
- Expo + Maestro E2E: <https://docs.expo.dev/eas/workflows/examples/e2e-tests/>
- Maestro docs: <https://docs.maestro.dev/>
- Hermes Intl APIs: <https://github.com/facebook/hermes/blob/main/doc/IntlAPIs.md>
- Android per-app language: <https://developer.android.com/guide/topics/resources/app-languages>
- Android dark theme: <https://developer.android.com/develop/ui/views/theming/darktheme>
- Material 3 color roles / dark: <https://m3.material.io/styles/color/roles>
- Android accessibility testing: <https://developer.android.com/guide/topics/ui/accessibility/testing>
- Play pre-launch report: <https://support.google.com/googleplay/android-developer/answer/9842757>
- Android vitals thresholds: <https://developer.android.com/topic/performance/vitals>
- Firebase Test Lab (quotas, deprecation): <https://firebase.google.com/docs/test-lab>
- RN decimal-pad comma issues: <https://github.com/facebook/react-native/issues/22005>,
  <https://github.com/facebook/react-native/issues/21733>
- Unicode CLDR: <https://www.unicode.org/cldr/charts/latest/>
- Microsoft localization style guides (pt-BR, pt-PT, es-MX, Spanish neutral):
  <https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides>
- NetInfo / expo-network reachability (`null` = unknown): <https://docs.expo.dev/versions/latest/sdk/network/>
