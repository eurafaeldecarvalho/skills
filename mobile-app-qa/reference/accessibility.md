# Accessibility (dimension 7)

- Touch targets ≥ 48×48 dp (use `hitSlop` for small icons); spacing between targets.
- Every interactive element has `accessibilityRole` and a **localized** `accessibilityLabel` (icon-only
  buttons!), state (`accessibilityState` selected/checked/disabled), and hints where non-obvious.
- TalkBack pass on a real phone: complete the core flows eyes-closed; logical focus order; headers marked
  (`accessibilityRole="header"`); errors announced (`AccessibilityInfo.announceForAccessibility` or live
  regions); modals trap focus; no unlabeled "button button".
- Contrast: 4.5:1 text, 3:1 large text/icons/borders, in light **and** dark.
- Font scale 2.0 and display size largest: nothing clipped, nothing overlapping (sweep covers it).
- Don't convey meaning by color only (balances: sign + word, not just red/green).
- Respect reduce motion (`AccessibilityInfo.isReduceMotionEnabled`) for big animations.
- Tools: Accessibility Scanner app (Android), `uiautomator dump` bounds (sweep detector `small-target`),
  Play pre-launch accessibility warnings, RNTL `getByRole`/`getByLabelText` queries in component tests
  (if a test can't find it by role/label, TalkBack can't either).
Scoring: 4 = core flows done with TalkBack + font 2.0 on a real phone, no warnings untriaged.
