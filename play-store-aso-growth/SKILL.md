---
name: play-store-aso-growth
description: >-
  A practical playbook for getting an Android app found, installed and shared on Google Play: how Play
  search and ranking actually work (ASO, "SEO da Play Store"), how to write and test the store listing,
  how to get from the mandatory closed test to production, how to earn ratings without breaking policy,
  which Android vitals and core-value thresholds quietly cut your visibility, and which growth loops
  (invites, shareable artifacts, deep links, web/short-video/community) make an app spread. Use it when
  preparing a Play Store listing or launch, when an app "has no installs" or stopped growing, when picking
  keywords, writing a title/short/full description, planning screenshots or an A/B test, designing a
  referral or invite loop, deciding whether to pay for Google Ads App campaigns, or checking a listing for
  policy risks before submitting. Every rule is tagged [FACT] (with a Google source) or [HEURISTIC]
  (industry practice). Validate first that the concept has a reason to spread; ASO only amplifies demand.
---

# Play Store ASO + growth (find → convert → keep → spread)

A field guide for one person shipping an Android app on Google Play in 2025-2026. It turns what Google
officially says about Play search, the store listing and quality signals into a checklist, and adds the
industry practice that fills the gaps Google keeps proprietary.

**The model in one line.** Play shows your app to people when it is **relevant** to what they search or
browse (text + category + behavior) and **good** for them (installs that stick, ratings, technical quality,
core value). Text gets you *considered*; conversion, retention and quality decide whether you *stay* there.
Nobody outside Google knows the weights. Google says ranking is "based on a combination of ratings,
reviews, downloads, and other factors" and that it "factors in the overall experience of your app based on
user behavior and feedback" ([Get discovered on Google Play search][discover]).

**Evidence tags used below**
- **[FACT]**: stated by Google (Play Console Help, Android Developers, Play Console guides). Link given.
- **[HEURISTIC]**: consensus of ASO vendors and practitioners (AppTweak, MobileAction, Phiture, etc.).
  Useful, but not confirmed by Google. Treat numbers as starting points to test, not rules.
- **💲**: costs money.

Facts verified on **2026-10-29**. Play changes often; re-check thresholds and limits before relying on them.

**Files in this folder**

| File | What it is |
|---|---|
| `SKILL.md` | The playbook (this file) |
| `listing-template.md` | Fill-in template for a store listing + keyword sheet + pre-submit policy check |

---

## 0. Order of work (do not skip ahead)

1. **Concept has a reason to spread** (validate the concept first). ASO cannot fix an app nobody needs.
2. **Quality floor**: no crash/ANR above the bad-behavior thresholds (section 5). Bad vitals cap everything else.
3. **Listing that converts** (sections 1-3): keywords in the right fields, icon + screenshots that sell.
4. **Closed test → production** (section 6), collecting the first honest ratings.
5. **Loops** (section 8): every user brings the next user. This is where "viral" actually comes from.
6. **Measure and iterate** (section 9): A/B test the listing, watch retention, re-do keywords monthly.
7. **Paid acquisition only last** 💲 (section 10), and only once retention proves the users are worth buying.

---

## 1. How Play reads your text (indexing)

| Field | Limit | Indexed for search? | Role |
|---|---|---|---|
| App name (title) | **30 chars** [FACT][metadata] | Yes, strongest signal [HEURISTIC][apptweak-kw] | Brand + #1 keyword |
| Short description | **80 chars** [FACT][bestpractices] | Yes [HEURISTIC][apptweak-checklist] | Shown under the listing and in places like search; conversion first |
| Full description | **4,000 chars** [FACT][bestpractices] | Yes (unlike the iOS description) [HEURISTIC][apptweak-desc] | Keyword coverage + explanation |
| Developer name | — | Shown with title; treat as indexed [HEURISTIC] | Same no-emoji / no-ranking rules as the title [FACT][metadata] |
| Keyword field | **Does not exist on Play** [HEURISTIC, universally reported][apptweak-kw] | — | All keywords must live in visible text |
| Screenshot alt text | per image | Accessibility [FACT][discover] | Describe each screenshot in 1-2 sentences |
| Category / tags | — | Context for relevance [HEURISTIC] | Pick the category your competitors rank in |

**What Google says about text** [FACT][discover]:
- Title: unique, focused, "avoid common terms", no subtle misspellings, no excessive emoji/ASCII.
- Description: "Use SEO best practices" but mind the spam policy; put the most important text where users do
  not have to scroll; focus on what the user gets.
- Short description: summarize the biggest benefit; **don't repeat it inside the full description**
  [FACT][bestpractices].
- Machine translation is automatic for languages you don't define, but human-written translations
  "can lead to better search results and discoverability" [FACT][discover].

**Keyword density** [HEURISTIC]:
- AppTweak: primary keyword around **2-3%** of the full description, secondary **1-2%**; in practice the
  primary term **3-5 times** and each secondary **1-3 times** in a full-length description, front-loaded in
  the first paragraph, bullets and headers ([AppTweak][apptweak-kw], [AppTweak][apptweak-desc]).
- Long-tail variants ("sleep tracker", "sleep cycle tracker") let you hit density without repetition.
- Google's own line is the ceiling: "Avoid using repetitive or unrelated keywords", and "excessive length,
  detail, improper formatting, or repetition can result in a violation" [FACT][metadata]. When density and
  readability conflict, readability wins.
- Play's search understands synonyms and related terms reasonably well (ML-based) [HEURISTIC][sel]; write
  for meaning, then make sure your exact head term appears.

**Off-store signals** [HEURISTIC]: links to your Play listing from relevant websites (with descriptive
anchor text) are widely reported to help Play ranking ([Search Engine Land][sel]). A real website with
App Links / deep links into your app is good for users and for Google Search either way.

---

## 2. Listing optimization checklist

### Text
- [ ] **Title (≤30)**: `Brand: main keyword` or `Brand – main benefit`. One head keyword, no stuffing.
- [ ] No emoji, emoticons, repeated special characters, ALL CAPS (unless brand) in title, icon or developer
      name [FACT][metadata].
- [ ] No ranking/performance words: "#1", "Best", "Top", "App of the year", "Popular" [FACT][metadata].
- [ ] No price/promo words in title, icon or short description: "free", "10% off", "discount"
      [FACT][metadata], [FACT][bestpractices].
- [ ] No reference to Play programs: "Editor's Choice", "New" [FACT][metadata].
- [ ] **Short description (≤80)**: the biggest benefit + 1-2 keywords, in plain words.
- [ ] **Full description (≤4,000)**: hook in the first 2-3 lines (visible without scrolling) → who it's for →
      3-6 benefit sections with headers/bullets → social proof (attributed only) → support/contact.
- [ ] No **unattributed or anonymous testimonials** ("best app ever – a user") [FACT][metadata].
- [ ] No comparison tables against other apps/brands, no word blocks or keyword lists [FACT][metadata].
- [ ] No other brand's or celebrity's name/logo without permission [FACT][metadata].
- [ ] Description matches what the app actually does [FACT][metadata].

### Graphics (conversion; screenshots don't appear in Play search results [HEURISTIC][sel], so icon + title carry search)
- [ ] **Icon** 512×512 32-bit PNG, ≤1 MB [FACT][assets]. Simple shape, readable at small size, no badges
      like a fake notification dot or "download" arrow [FACT][metadata], no text that claims ranking.
- [ ] **Feature graphic** 1024×500, JPEG or 24-bit PNG (no alpha) [FACT][assets]. Required for video;
      shown prominently on the listing.
- [ ] **Screenshots**: minimum 2; for apps to be eligible for promotion/recommendation surfaces Play asks for
      **at least 4 screenshots ≥1080 px** (e.g. 1080×1920 portrait) [FACT][assets].
      Games: three 16:9 landscape 1920×1080 [FACT][assets].
- [ ] Screenshot 1-2 tell the whole story (benefit caption + real UI). Order matters more than count
      [HEURISTIC].
- [ ] Unique **alt text** for every screenshot [FACT][discover].
- [ ] Tablet / foldable / Chromebook screenshots if you support them (ratings and promotion are now
      per form factor, see section 4) [FACT][discover].
- [ ] **Promo video** (YouTube, public): optional; the first seconds must show the product, not a logo
      [HEURISTIC].
- [ ] Screenshots and video show the real app experience [FACT][metadata].

### Settings that change who sees you
- [ ] Category chosen like your top competitors.
- [ ] Content rating questionnaire done (unrated apps may be removed) [FACT][appcontent].
- [ ] Privacy policy URL: public, HTTPS, not a PDF, specific to the app [FACT][appcontent].
- [ ] "Contains ads" declared truthfully (misdeclaring can get the app suspended) [FACT][appcontent].
- [ ] Data safety form accurate.

---

## 3. Localization, custom store listings and A/B tests

**Localization** [FACT]
- Add your own translations for every market you care about. Auto-translation covers the rest but your own
  text ranks better [FACT][discover].
- Localize keywords, not just sentences: people in pt-BR search with different words than in pt-PT or es-419
  [HEURISTIC].

**Custom store listings (CSL)** [FACT][csl] — up to **50** per app, each with its own name, icon,
descriptions and graphics (contact, privacy policy and category stay shared). Targeting options:
- Country/region (a country can be in only one CSL at a time).
- **Search keywords**: show a tailored listing to people who reached you with specific search terms
  (Play suggests keywords that already bring traffic; Gemini can draft the text).
- **Unique URL**: `https://play.google.com/store/apps/details?id=<package>&listing=<param>` — one per
  landing page, influencer, community post or campaign. Great for measuring channels and matching the
  message the visitor just saw.
- **Google Ads traffic** (by AdGroupID; currently shows mainly on AdMob traffic) 💲.
- **Pre-registration** users, **churned / lapsed** users, non-buyers / one-time / repeat / lapsed buyers,
  and custom audiences.
- CSLs are **not** auto-translated: add every language spoken in the targeted countries.

**Store listing experiments (A/B)** [FACT][experiments]
- One **default graphics** experiment (icon, feature graphic, screenshots, video) *or* up to **5 localized**
  experiments (graphics **and** short/full description) in up to 5 languages each, at the same time.
- Target metric: unique-user **install clicks**, open clicks, or pre-registration clicks. Console estimates
  time to significance.
- Also available for pre-registration listings [FACT][academy-prereg].
- Google's best practice: **test one attribute at a time**, run **≥7 days** (weekday + weekend), test
  **≥3 alternatives**, start with the **icon**, then screenshots and short description, then feature graphic
  [FACT][academy-prereg].
- Low-traffic reality [HEURISTIC]: under a few hundred listing visitors a week, tests won't reach
  significance. Test only big differences (different concept, not different shade), and use CSL URLs from
  your own channels to learn faster.

---

## 4. Ratings and reviews

**How the rating works** [FACT]
- The rating shown on Play is **weighted toward recent ratings**, not a lifetime average
  [FACT][ratings-help]. A bad release shows up fast; so does a fix.
- Users see the rating **for their registered country** (phones, since Nov 2021) and **for their device
  form factor** (tablets/foldables, ChromeOS, Wear, Auto, since 2022) [FACT][ratings-blog].
- Ratings "are taken into consideration for featuring and placement on Play Store" [FACT][ratings-blog].

**Asking for ratings the right way** [FACT][inapp-review]
- Use the **Play In-App Review API** (the native card; the user never leaves the app).
- Trigger it **after the user has experienced enough value** (e.g. after a completed task, a successful
  invite, the 3rd session), never on first open, never mid-task.
- **Do not ask any question before the card** ("Do you like the app?", "Would you give 5 stars?") — no
  pre-filtering/"review gating" [FACT][inapp-review].
- Don't modify, overlay or programmatically dismiss the card.
- There is an undisclosed **quota** (calling more than once in about a month may show nothing). So **never
  put the API behind a "Rate us" button**; for a button, link to the Play listing instead.

**Policy: forbidden** [FACT][ratings-policy]
- Any reward, discount, coins, unlock or other incentive for a rating or review.
- Fake reviews, review swaps, paying services, employees/friends posting as users, repeated ratings.
- Forced or deceptive rating pop-ups.
- Incentivized installs to manipulate ranking are detected, filtered (removed from top charts) and can
  lead to removal; Google's research found incentivized users retain worse and spend less
  [FACT][incentivized-blog].

**Reply to reviews** [FACT][ratings-policy]
- Answer the issue, link to help/FAQ, never ask for a higher rating in the reply.
- [HEURISTIC] Reply to every 1-3★ review within 24-48 h, ship the fix, then reply again saying it is
  fixed — users often update their rating. Track rating per version in Console (breakdowns by country,
  version, device) [FACT][ratings-help].

---

## 5. Quality signals that quietly cut visibility (Android vitals + core value)

Play says core vitals "affect the discoverability of your app" and that apps over the bad-behavior
thresholds are "likely to be less discoverable", may be **steered away from on specific device models**,
and may get a **warning on the store listing**. Evaluation normally uses the last **28 days**, sooner on a
spike [FACT][vitals].

| Metric | Bad-behavior threshold [FACT][vitals] |
|---|---|
| User-perceived **crash** rate (overall) | **≥ 1.09%** of daily users |
| User-perceived **ANR** rate (overall) | **≥ 0.47%** of daily active users |
| Crash or ANR rate on a **single device model** | **≥ 8%** |
| Excessive partial wake locks (beta) | > 5% of battery sessions with >3 h of wake locks (beta: no discoverability effect yet) |
| Watch face battery | > 1% of sessions |

**Core value metrics** (the closest thing to an official retention/uninstall signal) [FACT][vitals]:
- **DAU/MAU below 8%** → a warning may be shown on your listing and the app "may not be eligible to appear on
  certain surfaces on Google Play".
- **User loss rate above 5%** (users who uninstalled from all devices vs users with it installed on an
  active device) → same consequences.

Also watched (no stated ranking penalty, but they hurt reviews and retention): slow cold start ≥5 s,
excessive slow/frozen frames, LMKs, permission denials [FACT][vitals]. The featuring guide adds: "If your
title exceeds Google Play's bad behavior threshold on specific phones or tablets, we will not promote your
title to users on those devices" [FACT][featuring].

**Checklist**
- [ ] Run the **pre-launch report** on every test-track build (free device lab) [FACT][testing].
- [ ] Crash reporting in the app (Firebase Crashlytics or similar) in addition to vitals.
- [ ] Watch Android vitals weekly; set anomaly notifications [FACT][vitals].
- [ ] Use staged rollouts (e.g. 10% → 50% → 100%) so a bad build hurts few users [HEURISTIC].
- [ ] Onboarding gets the user to the core value in the first session; that is what moves DAU/MAU and user
      loss [HEURISTIC].

---

## 6. Launch plan: from closed test to production

**New personal developer accounts** (created after 13 Nov 2023) [FACT][testing]:
- Must run a **closed test with ≥12 testers opted in continuously for ≥14 days** before they can apply
  for production. Pre-registration also stays locked until then.
- Opt-out and back in restarts that tester's count; the 14 days must be consecutive.
- Then **Apply for production** on the Dashboard: questions about the test (how testers were recruited,
  engagement, feedback summary), the app (audience, value, expected installs) and readiness (what you
  changed). Review usually ≤7 days. Insufficient engagement → "continue testing".
- The rule is stated for personal accounts; organization accounts are not listed under it.
- 💲 Play developer registration is a one-time **US$25** fee [FACT][reg].

**Week-by-week plan** [HEURISTIC, built on the facts above]

| When | Do |
|---|---|
| T-6 weeks | Keyword research (section 7); draft listing with `listing-template.md`; build share/invite loop (section 8) into v1, not later. |
| T-5 | Internal test (instant, no review) with yourself + 2-3 people; fix crashes; pre-launch report. |
| T-5 → T-3 | **Closed test**: recruit 15-20 real target users (not 12: some drop). Communities where your users already are, friends of friends. A WhatsApp/Telegram group for feedback (Google suggests a tester messaging group [FACT][testing]). Ask them to use it for real for 14 days. Fix what they report and **write it down** — you will summarize it in the production application. |
| T-3 | Apply for production. Meanwhile: landing page with the Play badge, short-video content, waitlist. |
| T-2 → T-0 | Optional **pre-registration** (max **90 days**; pre-registered users get a push at launch and eligible devices get **auto-install**) [FACT][prereg]. A/B test the pre-registration listing [FACT][academy-prereg]. |
| Launch day | Production rollout; announce in every channel at once (concentrated install velocity [HEURISTIC]); reply to every review. |
| Weeks 1-4 | In-app review prompt live after the "aha" moment; daily vitals; first listing A/B test; first keyword re-check. |
| Monthly | Keyword re-check, new screenshots/test, "What's new" text on every update (regular updates are an official visibility lever) [FACT][discover]. |

**Install velocity** [HEURISTIC]: practitioners consistently see that a burst of organic installs plus
good conversion in a short window lifts keyword and chart rankings. Google does not publish this. Never fake
it (paid install farms = filtered + policy risk [FACT][incentivized-blog]). Concentrate real announcements
in the same days instead of trickling them out.

---

## 7. Keyword research workflow (free-first)

1. **Seed list (30-60 terms)**: how a user would describe the *problem*, not your feature names. Include
   pt-BR/en/es variants per market.
2. **Play's own autocomplete**: type each seed in the Play Store search box (phone, and logged-out web).
   Suggestions = real demand. Write them down.
3. **Competitors**: open the top 10 results for each seed; copy their titles/short descriptions into a sheet;
   count which terms repeat (these are the category's head terms).
4. **Google Trends** and Google Search autocomplete for relative volume and seasonality (free).
5. **Optional 💲 ASO tools** (AppTweak, MobileAction, Sensor Tower, AppFollow, Appfigures): volume/difficulty
   estimates. Paid plans; free trials exist. Treat their numbers as estimates.
6. **Score** each term: relevance (0-3) × estimated volume (0-3) ÷ difficulty (top-10 strength, 1-3).
   [HEURISTIC]
7. **Place**: 1 head term in the title; 1-2 in the short description; the rest across the full description
   at the density in section 1; very different intents → a search-keyword CSL (section 3).
8. **After launch**: Play Console → Store performance shows the **search terms that bring visitors and
   installs** (this replaces guessing). Re-weight monthly. Keep what converts, drop what only brings views.

Rule: a high-volume term where your listing converts badly is worse than a smaller term where it converts
well — low conversion is itself a negative relevance signal [HEURISTIC].

---

## 8. Growth and virality loops (where "going viral" really comes from)

ASO captures existing demand. Viral growth creates new demand: each user brings more users.

**The math** [HEURISTIC, standard growth model]: `K = invites sent per user × conversion of each invite`.
K > 1 means self-sustaining growth; most good consumer apps run at K 0.2-0.6, which still multiplies every
other channel by `1 / (1 − K)` (K = 0.5 → each acquired user is worth 2). Shorter **cycle time** (time from
install to the first invite accepted) matters as much as K.

**Loop types, best first for small apps**
1. **Two-sided by design (strongest)**: the app is only useful when another person joins. The invite is the
   product, not a growth hack. Example hypothetical: a co-parenting app where parent A creates the shared
   calendar and must invite parent B for it to work — every activated user produces one more install with
   very high intent. Make the invite the 2nd step of onboarding, pre-fill the message, allow WhatsApp/SMS/
   link, and show the inviter what they unlock when the other person joins.
2. **Shareable artifacts**: something the user *wants* to post — a result card, a summary image, a
   streak, a generated plan, a before/after. Watermark + short link to the Play listing (or to a CSL URL).
3. **Collaboration / content**: shared lists, groups, documents, events: non-users see content and a
   "get the app" path.
4. **Referral rewards** (in-app value for the inviter and/or invitee): allowed for **installs from real
   referrals that reward in-app value**, but **never** reward ratings or reviews [FACT][ratings-policy], and
   don't make "install other apps" the app's main function [FACT][ratings-policy]. Rewarded/incentivized
   installs used to game ranking get filtered [FACT][incentivized-blog].

**Plumbing** [FACT]
- **Play Install Referrer API**: securely read the `referrer` value from the Play URL
  (`https://play.google.com/store/apps/details?id=<package>&referrer=<url-encoded params>`) on first launch,
  with click and install timestamps [FACT][referrer]. Use it to credit the inviter and to open the right
  shared item after install (deferred deep link) without a third-party SDK.
- **Android App Links** for links that open the app when installed and fall back to the web/Play page.
- **CSL URLs** (`&listing=`) so a person invited for a specific reason lands on a listing that speaks to it
  [FACT][csl].

**Loop checklist**
- [ ] The invite/share moment is inside the core flow, right after value is delivered.
- [ ] The invited person sees *who* invited them and lands directly in the shared context.
- [ ] Measure: invites sent/user, invite→install, install→activation, cycle time (days).
- [ ] The inviter gets a notification when the invite converts (closes the loop, triggers more invites).

---

## 9. Cross-channel (free, compounding)

- **Website/landing page** per main use case (SEO on Google Search), each linking to its own CSL URL.
  [HEURISTIC]
- **Short video** (TikTok, Reels, YouTube Shorts): show the problem → the app solving it in <15 s; post
  consistently; the app's shareable artifact is the content [HEURISTIC].
- **Communities** where the audience already talks (Reddit, Facebook/WhatsApp groups, forums, Discord):
  contribute first, follow each community's self-promotion rules [HEURISTIC].
- **PR / niche creators / newsletters**: a story ("built by a parent for parents") beats a feature list
  [HEURISTIC].
- **Play surfaces** [FACT]:
  - **Promotional content** (former LiveOps): events, offers, major updates on your listing and possibly
    Play home/search. Available for **all games**, but for **apps only if eligible for Premium growth
    tools** — standard thresholds are large (e.g. ~1.6M MAU or tens of thousands of USD monthly spend)
    [FACT][promo], [FACT][pgt]. Most new apps cannot use it yet.
  - **Featuring**: Play says apps must be good quality for more discovery and **great** quality for
    featuring, judged on core value, UX, technical quality, privacy; plus listing and promotional assets
    [FACT][featuring]. There is no guaranteed nomination route for a new free app; featuring requests run
    through Promotional content quotas for eligible developers [FACT][promo]. (The featuring guide page
    also lists an interest form for discounted premium/paid titles, as seen on 2026-10-29.)
  - **Google Play Points**: coupon/in-app promotions for eligible titles, mostly games [FACT][playpoints].
  - **Pre-registration** + launch push + auto-install [FACT][prereg].
- **Editors' Choice / "Best of" awards** are editorial; you cannot apply, and you may not mention them in
  your metadata [FACT][metadata].

---

## 10. Paid: Google Ads App campaigns 💲

- Google's own minimum: daily budget **≥ 50 × target CPI** for install campaigns (e.g. target CPI US$0.50 →
  US$25/day), ≥10× for target-CPA [FACT][ads].
- Use only after you know Day-1/Day-7 retention and that users who arrive stay; buying installs into a
  leaky app only raises user loss rate (section 5).
- Point each ad group to a matching **ads-targeted CSL** [FACT][csl].
- Small-budget alternative: boost your best-performing organic short video as an ad to a lookalike audience
  [HEURISTIC].

---

## 11. Metrics to watch

| Metric | Where | Why |
|---|---|---|
| Store listing visitors → **acquisition conversion rate** (by source, country, search term) | Play Console → Store performance | Listing quality; compare with category peers |
| Search terms bringing visitors/installs | Store performance | Real keyword data for section 7 |
| User-perceived crash / ANR rate (and per device) | Android vitals | Thresholds in section 5 |
| **DAU/MAU** (≥8%) and **user loss rate** (≤5%) | Android vitals → core value | Official visibility/surface eligibility |
| Rating per country / version / device | Ratings and reviews | What users actually see |
| D1 / D7 / D30 retention | Your analytics | Leading indicator for everything |
| K-factor, invite→install, cycle time | Your analytics + Install Referrer | Virality |
| Install velocity around launches/updates | Statistics | Correlate with ranking moves |

---

## 12. Things that get apps rejected, demoted or removed

| Don't | Why |
|---|---|
| Keyword stuffing, keyword lists, word blocks, irrelevant keywords | Metadata policy [FACT][metadata] |
| "Best", "#1", "Top", "Popular", "App of the year", award icons in title/icon/name/screens | Store performance claims banned [FACT][metadata] |
| "Free", "% off", "limited time" in title/icon/developer name/short description | Price/promo claims banned [FACT][metadata], [bestpractices] |
| Emoji, emoticons, repeated symbols, ALL CAPS in title/icon/developer name | [FACT][metadata] |
| Unattributed testimonials; competitor comparisons; others' brands/celebrities | [FACT][metadata] |
| Fake notification dots or download arrows on the icon | Misleading symbols [FACT][metadata] |
| Rewards for ratings; review gating; forced/deceptive rating prompts; bought reviews | [FACT][ratings-policy], [inapp-review] |
| Paid install farms / incentivized installs to move ranking | Filtered, removed from charts, can be removed [FACT][incentivized-blog] |
| Screenshots/video that don't show the real app; misleading claims | [FACT][metadata] |
| Wrong ads declaration, missing privacy policy, missing reviewer login | [FACT][appcontent], [testing] |
| Pre-registration reward promised and not delivered | Can lead to suspension [FACT][prereg] |
| Closed test with friends who never open the app | Production access denied / more testing [FACT][testing] |

---

## 13. Final pre-submit gate

- [ ] Title ≤30, short ≤80, full ≤4,000; no banned words/symbols (section 12).
- [ ] Head keyword in title, 1-2 in short description, natural density in full description.
- [ ] Icon + ≥4 screenshots ≥1080 px + feature graphic; alt text on each.
- [ ] Translations for each target market; CSLs for distinct audiences/channels.
- [ ] Vitals under thresholds on the test track; pre-launch report clean.
- [ ] In-app review triggered after value, no pre-question, not behind a button.
- [ ] Invite/share loop + Install Referrer wired and measured.
- [ ] One A/B test planned for the first 2 weeks after launch.
- [ ] Any money spent is listed with a reason (ASO tool, ads, translation).

---

## Sources

Primary (Google):
- [discover]: Get discovered on Google Play search — https://support.google.com/googleplay/android-developer/answer/4448378
- [metadata]: Metadata policy — https://support.google.com/googleplay/android-developer/answer/9898842
- [bestpractices]: Best practices for your store listing — https://support.google.com/googleplay/android-developer/answer/13393723
- [assets]: Add preview assets (graphics specs) — https://support.google.com/googleplay/android-developer/answer/9866151
- [csl]: Custom store listings — https://support.google.com/googleplay/android-developer/answer/9867158
- [experiments]: Store listing experiments — https://support.google.com/googleplay/android-developer/answer/12053285
- [academy-prereg]: Play Academy, pre-launch features and experiment best practices — https://playacademy.exceedlms.com/student/page/454856-program-benefits-and-features-for-pre-launch-confidence
- [ratings-help]: View and analyze ratings and reviews — https://support.google.com/googleplay/android-developer/answer/138230
- [ratings-blog]: Making Ratings and Reviews better (Android Developers Blog, 2021) — https://android-developers.googleblog.com/2021/08/making-ratings-and-reviews-better-for.html
- [ratings-policy]: User Ratings, Reviews, and Installs policy — https://support.google.com/googleplay/android-developer/answer/9898684
- [incentivized-blog]: Play's policy on incentivized ratings, reviews and installs (2017) — https://android-developers.googleblog.com/2017/06/google-plays-policy-on-incentivized.html
- [inapp-review]: In-App Review API — https://developer.android.com/guide/playcore/in-app-review
- [vitals]: Android vitals (core vitals, thresholds, core value) — https://support.google.com/googleplay/android-developer/answer/9844486
- [testing]: Testing requirements for new personal accounts — https://support.google.com/googleplay/android-developer/answer/14151465
- [prereg]: Pre-registration — https://support.google.com/googleplay/android-developer/answer/9084187
- [promo]: Promotional content — https://support.google.com/googleplay/android-developer/answer/12932541
- [pgt]: Premium growth tools — https://play.google.com/console/about/guides/premium-growth-tools/
- [featuring]: Getting featured on Google Play — https://play.google.com/console/about/guides/featuring/
- [playpoints]: Google Play Points for developers — https://support.google.com/googleplay/android-developer/answer/10366692
- [referrer]: Play Install Referrer — https://developer.android.com/google/play/installreferrer
- [appcontent]: Prepare your app for review (App content) — https://support.google.com/googleplay/android-developer/answer/9859455
- [reg]: Play Console registration fee — https://support.google.com/googleplay/android-developer/answer/6112435
- [ads]: Google Ads App campaign budget/bidding — https://support.google.com/google-ads/answer/9176652

Industry (heuristics):
- [apptweak-kw]: AppTweak, How to add keywords on Google Play — https://www.apptweak.com/en/aso-blog/how-to-add-keywords-to-apps-on-google-play
- [apptweak-desc]: AppTweak, App description best practices — https://www.apptweak.com/en/aso-blog/app-store-description-best-practices
- [apptweak-checklist]: AppTweak, ASO checklist for Google Play — https://www.apptweak.com/en/aso-blog/app-store-optimization-aso-checklist-for-google-play
- [sel]: Search Engine Land, App Store vs Google Play ASO — https://searchengineland.com/app-store-vs-google-play-aso-strategy-450983

[discover]: https://support.google.com/googleplay/android-developer/answer/4448378
[metadata]: https://support.google.com/googleplay/android-developer/answer/9898842
[bestpractices]: https://support.google.com/googleplay/android-developer/answer/13393723
[assets]: https://support.google.com/googleplay/android-developer/answer/9866151
[csl]: https://support.google.com/googleplay/android-developer/answer/9867158
[experiments]: https://support.google.com/googleplay/android-developer/answer/12053285
[academy-prereg]: https://playacademy.exceedlms.com/student/page/454856-program-benefits-and-features-for-pre-launch-confidence
[ratings-help]: https://support.google.com/googleplay/android-developer/answer/138230
[ratings-blog]: https://android-developers.googleblog.com/2021/08/making-ratings-and-reviews-better-for.html
[ratings-policy]: https://support.google.com/googleplay/android-developer/answer/9898684
[incentivized-blog]: https://android-developers.googleblog.com/2017/06/google-plays-policy-on-incentivized.html
[inapp-review]: https://developer.android.com/guide/playcore/in-app-review
[vitals]: https://support.google.com/googleplay/android-developer/answer/9844486
[testing]: https://support.google.com/googleplay/android-developer/answer/14151465
[prereg]: https://support.google.com/googleplay/android-developer/answer/9084187
[promo]: https://support.google.com/googleplay/android-developer/answer/12932541
[pgt]: https://play.google.com/console/about/guides/premium-growth-tools/
[featuring]: https://play.google.com/console/about/guides/featuring/
[playpoints]: https://support.google.com/googleplay/android-developer/answer/10366692
[referrer]: https://developer.android.com/google/play/installreferrer
[appcontent]: https://support.google.com/googleplay/android-developer/answer/9859455
[reg]: https://support.google.com/googleplay/android-developer/answer/6112435
[ads]: https://support.google.com/google-ads/answer/9176652
[apptweak-kw]: https://www.apptweak.com/en/aso-blog/how-to-add-keywords-to-apps-on-google-play
[apptweak-desc]: https://www.apptweak.com/en/aso-blog/app-store-description-best-practices
[apptweak-checklist]: https://www.apptweak.com/en/aso-blog/app-store-optimization-aso-checklist-for-google-play
[sel]: https://searchengineland.com/app-store-vs-google-play-aso-strategy-450983
