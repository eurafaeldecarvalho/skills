# APP-QA.md — context for mobile-app-qa (keep in the app repo at qa/APP-QA.md)

- App / package id: `com.example.app` · repo path: · stack: Expo SDK __ / RN __ / backend __
- Who uses it, where: (countries, languages, typical phones — e.g. "parents in BR on Moto G/Galaxy A")
- Shipped locales (language → format locale → currency): e.g. pt-BR → pt-BR → BRL; es → es-AR → ARS
- Themes: system / light / dark (in-app override? y/n)
- Roles & accounts: (owner, co-parent, viewer…) · test accounts: in password manager / CI secrets (never here)
- Critical flows (money, permissions, destructive, legal): …
- Build: release command, how to get an APK, signing (no secrets here)
- Devices available: emulator AVDs, real phones (model, Android version, skin)
- Constraints: shared machine? → `BOX_PROJECT=<name>`, booked slots in `/home/box/shared/box-schedule.md`
  (`scripts/box-reserve.sh`); budget (no paid services without approval)
- Known issues / tester reports: link to bug list
- Last QA run: date, build, gate result
