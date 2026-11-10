# MediaTracker Dev Log

A record of every change to this repo and why it was made. Every commit adds an entry, included in the commit itself. Add new entries at the top of the log, directly under the `## Log` heading.

Merge commits don't need an entry, because the commits they bring in already have one.

### Entry format

```markdown
### YYYY-MM-DD: Short title
**Author:** Name

**What changed:** The files or behaviour affected, in plain language.

**Why:** The reason for the change, including any decision or trade-off behind it.
```

## Log


### 2026-11-06: Notifications page, bell in the top bar, and a Me section with name and username
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `social/selectors.py`, `social/views.py`, `social/urls.py`, new `social/templates/social/notifications.html`, `core/templates/core/shell.html`, `core/templatetags/ui.py` (bell icon), `member/forms.py`, `member/views.py`, `member/urls.py`, `member/templates/member/settings.html`, `core/static/core/js/app.js`, `core/static/core/css/app.css`. A bell now sits beside the settings cog on the profile's top bar and opens a notifications page built from the live tables: new followers, likes and comments on your posts, stickers received, bounties set on you, newest first, with seen-state kept in the session. The settings Avatar section is now "Me": the avatar circle is a button that reveals the picture picker (upload, stock, remove) on tap, and name and username are editable with a Save button (`member:profile`, ModelForm on display_name and username).

**Why:** Kyle wanted notifications reachable from the top bar and the identity fields editable where the avatar lives, with the avatar picker out of the way until the circle is tapped.


### 2026-11-06: Bigger buddy on the level line
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_profile.html`, `core/static/core/css/app.css`. The hero buddy portrait is 96px (72px under 420px), up from 80px/56px.

**Why:** Kyle wanted the buddy beside the level more prominent.


### 2026-11-06: Compact bounty card with the whole poster behind the bars
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_bounty_card.html`, `core/static/core/css/app.css`. The bounty card is a row again: the complete poster (contain, never cropped) sits on the left at 60x90 with the prison-bars overlay on the poster itself, and the terms and Collect/Cancel actions sit beside it. Buttons shrank to match the smaller card.

**Why:** The full-bleed version cropped most of every cover; Kyle wanted the whole image visible and the card smaller.


### 2026-11-06: CHUD hero fits narrow phones
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `core/static/core/css/app.css`. Under 420px the hero's level line drops to 22px, the points pill stops wrapping, and the buddy portrait shrinks to 56px.

**Why:** With the buddy portrait back beside the level, "CHUD Level 6" and the points pill wrapped to two lines at phone width.


### 2026-11-06: Bounty cards show the full cover behind the bars again
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_bounty_card.html`, `core/static/core/css/app.css`. The tap-to-reveal is gone: the card is again the full-bleed cover with the dark scrim and always-visible terms (tag, time left, title, from/for line), now with a prison-bars overlay between the image and the scrim. The Collect button (received) and Cancel bounty button (sent) stay visible on the card.

**Why:** Kyle wanted the whole cover visible like the earlier design, with the bars kept and the actions no longer hidden behind a tap.


### 2026-11-06: Settings UI tightened
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `member/templates/member/settings.html`, `core/static/core/css/app.css`. Every settings section is now an inset card. The avatar upload became one "Upload picture" button that submits on file pick (reuses the `data-autosave` change-to-submit path), replacing the native file input plus separate Upload button. The CHUD buddy strip no longer renders on settings; it stays on the profile where it belongs.

**Why:** The page read as a form dump: naked sections, a two-step upload, and a game picker with locked tiles sitting in the middle of settings.


### 2026-11-06: Bounty cards are posters behind prison bars; tap reveals terms
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_bounty_card.html`, `core/static/core/css/app.css`. A collapsed bounty card is the full cover image with a prison-bars overlay, a Bounty badge and a time-left chip. It is now a native `details` element: tapping (no JS, CSP-safe) expands to show the bounty terms with a Collect button on received bounties (links to the title, where logging settles it) and a Cancel bounty button on sent ones.

**Why:** Kyle wanted the cover as a full poster behind literal prison bars, with the terms and actions hidden behind a tap instead of always visible.


### 2026-11-06: Bounties sit above the CHUD activity header
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_profile.html`. The bounty cards moved out of the activity section into their own block directly after Stickers, above the "CHUD activity" heading. The hidden `#chud-bounties` OOB target stays for HTMX swaps.

**Why:** Kyle wanted bounties first, before the activity list heading.


### 2026-11-06: Bounty cards use their cover as the backdrop
**Author:** Kyle Deboo (with CORTEX)

**What changed:** New `chud/templates/chud/_bounty_card.html` include (used by `_profile.html` and `_bounties_changed.html`, which previously duplicated the card markup), plus `core/static/core/css/app.css`. A bounty card is now a full-bleed cover image with a dark gradient scrim, the bars icon and Bounty tag over it, and an amber outline on both received and sent bounties (sent is dimmer).

**Why:** Kyle wanted the cover image visible with the bars over it and an outline on both types; the sent variant's flat hairline row looked disconnected from the received card.


### 2026-11-06: Active buddy back beside the level
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_profile.html`, `core/static/core/css/app.css`. The hero keeps one large portrait of the active buddy beside the level text. The buddy section stays as the strip only, with the active buddy's name under its small tile.

**Why:** After removing both large portraits, Kyle wanted the hero visual back: the active buddy lives next to the level, the strip stays the picker with names.


### 2026-11-06: One buddy visual on the profile
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_profile.html`, `chud/templates/chud/_buddy_section.html`, `chud/selectors.py`, `core/static/core/css/app.css`, `chud/tests/test_screens.py`. The CHUD hero no longer renders a large buddy portrait, and the buddy section dropped its large display block. The active buddy's name now sits under its small tile in the strip (caption replaces the old "Active" label).

**Why:** Kyle saw two large Couch Goblins stacked on the profile. One small tile with the name underneath reads cleaner and keeps the strip as the single source of buddy state.


### 2026-11-06: Fix gifted stickers not appearing in recipient's collection
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/services.py`, `chud/tests/test_spending.py`. `send_sticker` never wrote a `UserSticker` row for the recipient, so stickers gifted by others were invisible in the profile's sticker list despite showing on the post/comment. Added the missing `get_or_create`+increment. Also fixed `verify()` to count `GIFT_RECEIVED` entries for sticker ownership.

**Why:** Buy and send have different code paths; the send path was missing the ownership write.

### 2026-11-06: Fix gifted stickers not appearing in recipient's collection
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/services.py`, `chud/tests/test_spending.py`. `send_sticker` never wrote a `UserSticker` row for the recipient. Added the missing ownership write and fixed `verify()` to count `GIFT_RECEIVED` entries for sticker ownership.

**Why:** Buy and send have different code paths; the send path was missing the ownership increment.

### 2026-11-06: Remove level and XP circles from CHUD highlights
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `chud/templates/chud/_highlights.html`. Removed the level badge and XP progress ring from the compact CHUD highlights row. The row now shows only buddy and crown (if present). The full CHUD detail below still includes level, XP bar, and everything else.

**Why:** Level and XP are already prominent in the expanded CHUD detail below the highlights row.
### 2026-11-06: Fix cog icon SVG geometry
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `core/templatetags/ui.py`. The cog icon had its spokes sitting inside the center circle. Widened the hub and moved teeth to the rim so it reads as a gear at icon sizes.

**Why:** The original geometry put the spoke endpoints at a smaller radius than the hub, making them invisible. A gear needs the teeth outside the inner circle.

### 2026-11-06: Profile header left-aligned with gear icon, CHUD always visible
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `social/templates/social/profile.html`, `core/static/core/css/app.css`, `chud/templates/chud/_highlights.html`, `core/templatetags/ui.py`. Reverted the centred header to a left-aligned flex row (large avatar, name + stats beside it). Settings is now a cog icon next to the display name instead of an Edit profile button. CHUD detail is always expanded below the highlights row; the toggle was removed. Added a cog icon to the UI icon set.

**Why:** Centred layout was rejected. A gear icon is lighter than a button. CHUD detail should be visible by default rather than hidden behind a tap.

### 2026-11-06: Remove visibility controls from profile page, fix cog icon
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `social/templates/social/profile.html`, `core/templatetags/ui.py`. Removed the "Who can see your Library and posts" fieldset from the profile page since `default_visibility` is already in Settings > Preferences. Fixed the cog icon SVG: changed the center circle from `r="2.5"` to `r="3.5"` and shortened the outer spokes so the gear shape is legible at icon sizes.

**Why:** The visibility toggle on the profile was redundant. The original cog SVG had a center circle so small it read as a generic sun/circle pattern rather than a settings gear.

### 2026-11-06: Profile page Instagram-style redesign
**Author:** Kyle Deboo (with CORTEX)

**What changed:** `social/templates/social/profile.html`, `core/static/core/css/app.css`, `social/views.py`, `social/templates/social/_post_grid.html` (new), `chud/templates/chud/_highlights.html` (new). The profile layout was restructured to a centred Instagram-style layout: large centred avatar, stat row (logged/followers/following), compact CHUD highlights row with expandable detail, pill tabs for Posts/Watchlist/Library, and a 3-column poster thumbnail grid replacing the full-card post feed. Infinite scroll loads more grid items into the same grid container. Self-only settings and sign-out moved to the settings page (linked via Edit profile button).

**Why:** The old layout was a vertical stack with full post cards that felt like a feed, not a profile. Instagram's profile layout (centred avatar, stat row, highlights, tabbed content, thumbnail grid) is the reference users expect for a social profile surface, and CHUD's gamification fits naturally as a highlights strip.

### 2026-11-02: A 403 from MAL pauses MAL for five minutes
**Author:** Shahan B (with Claude Code)

**What changed:** `PacedClient` in `catalogue/upstream/base.py` has a `cooldowns` setting, which lists extra statuses that mean "slow down" and how long to stay away. `Mal` sets `{403: 300}`, so a 403 now stops every MAL call for five minutes, or for as long as a `Retry-After` header says. Other clients are unchanged, and a 403 from them is still a plain error. Added four tests to `catalogue/tests/test_clients.py` and a note to the README.

**Why:** MAL publishes no rate limit, and client developers report that it answers bursts with a 403. The client only backed off on 429 and 503, so a throttled worker would have kept calling MAL once a second from the home IP. Pausing loses nothing, because a failed title already falls back to AniList. The trade-off is that a bad client ID also pauses MAL instead of failing straight away, which is harmless because AniList covers the gap. Five minutes is a cautious guess, as MAL doesn't document a figure.

### 2026-11-02: Empty search uses the app's empty state
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/templates/catalogue/search_panel.html`, `core/views.py`, `core/static/core/css/app.css`. A search with no matches now renders the shared `core/components/empty.html` (search icon and the line "Nothing here matches" the query), the same component the People screen uses for its miss, and Search everywhere under it is a primary button in that case and a text link otherwise. The one-off `.results__empty` rule is gone.

**Why:** review pointed out that the previous fix gave this state a bare line of text, where the UX standard asks for a designed empty state and the app already has one. The existing acceptance tests for the copy still pass unchanged.

### 2026-11-02: seed_demo no longer crashes for a member who already follows people
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/management/commands/seed_demo.py`, and a test in `catalogue/tests/test_seed_demo.py`. The CHUD part of `seed_demo --library-for USER` sends stickers to the fake members' posts. Those posts are made by the feed part, which is skipped for a member who already follows anyone, so on a real account that had followed people the command died with `'NoneType' object has no attribute 'user'`. The CHUD part now gives the points and stops when the posts aren't there.

**Why:** found in the compose smoke, where I seeded after the new member had followed the demo members through the app. The new test failed before the fix (run red, then green). It is a screenshots-only command, so this is a small fix, but a crash with a traceback is a poor first impression for anyone trying the demo.

### 2026-11-02: Fidelity pass against the prototype, and the final screenshots
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- `core/static/core/css/app.css`: poster tile titles no longer break a long single word mid-word ("Oppenheime / r"): the tile margin goes from 9 to 7 px (the prototype's) and the title gets a slight negative letter-spacing. Text buttons ("Rate", "Drop"), the library status chips ("All") and the footer About link had visible widths under 44 px; each now has `min-width: 44px`. Added `.results__empty`.
- `catalogue/templates/catalogue/search_panel.html`: a typeahead with no matching titles and no matching people now says "Nothing here matches" the query, above Search everywhere. Before, the panel showed only the hint and the link, which read as broken. The prototype has no copy for this state, so it is the one place the build adds words to the prototype.
- `social/templates/social/sheets/edit_post.html`: the form lacked the `composer` class, so the caption and spoiler fields fell back to the browser's light inputs while the composer sheet's are dark. Same class as the composer now.
- Two tests in `catalogue/tests/test_acceptance.py` for the empty search copy (shown for a miss, absent for an empty box).
- `Docs/screenshots/`: regenerated from a fresh `seed_demo` (viewer named Sam, so nothing personal is in the repo): 44 images at 390x844 and 1440x900 covering home, currently, library with expanded seasons, feed with its poster, stats, hold and blurred episode slides, profile, store, search, title, show, episodes, settings, the import states and review, admin, login, redeem, reset, 404, and the quick log, rate, bulk, composer, gift, level-up, bounty and edit sheets.

**Why:** the build was side by side with the prototype's UI frame (rendered from the bundle in a headless browser) at 390x844 and drifted in only the places above. An automated pass over every screen for target size, text under 11.5 px, unlabelled controls, image alt, horizontal overflow and console errors found nothing else except the inline links in a feed post's banner ("Sam finished Dune"), which are text inside a sentence and left as they are. The Web Interface Guidelines checks against the CSS (focus-visible rings, no `transition: all`, reduced motion, touch-action, overscroll, tabular numbers) are all already met. Colour contrast was measured on text over flat backgrounds only; text on generated poster art can't be measured that way and was checked by eye. The desktop view is the phone column centred in the window, as the plan says (phone first, desktop the same app given room).

### 2026-11-02: M6 review fixes: the refresh window and lost first fetches
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/refresh.py`.
- `due()` cut the oldest `limit * 2` media (and `limit` shows) before putting airing first, so with a backlog bigger than the window an airing title fetched eight days ago never made it in, and titles nothing could be asked about (TMDB with no key) filled the window before being thrown out. Airing and the rest are now queried separately, each oldest first and cut to the room left, for media and for shows, and unroutable sources are excluded in SQL.
- A refresh job that picked up a lost first fetch never cleared `details_pending`, so the title page went back to "Fetching details" and then "Couldn't fetch the details" on a row that had its details. All three refresh jobs now clear it in the same transaction as the write, and a flagged failure clears it too (`_flag`).

**Why:** both were found in review and are real: the first breaks "airing titles ahead", the second turns a good refresh into a visible error. Six new tests in `test_refresh.py` (backlog bigger than the window, `limit=1`, unroutable rows, an airing show, a lost stub on success, on failure, and a lost TMDB row) fail on the previous `refresh.py` and pass now. Only `test_refresh.py` and `test_hardening.py` were run this turn, by request.

### 2026-11-02: M6 resource check, README, screenshots and licence
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- `requirements.txt`: **Pillow** (`~=13.0`) added. Avatars are re-encoded to a 256 px WebP so a member's upload can't carry metadata, a hostile payload or a bomb into storage. The compose smoke caught that the first M6 commit imported it without listing it (the venv I tested in had it, the image did not); the image now builds and starts with it.
- `README.md` rewritten for a stranger: what you need, install, every environment variable in one table, backup and restore (the dump and restore commands were run against a throwaway Postgres 16 and came back with the data), what export and account deletion do (and what happens to stickers and bounties), the daily refresh, resource use, security notes, a note on similarly named projects, licence. `LICENSE` is MIT, "MediaTracker contributors" because the plan names no author; Shahan should put the name he wants there.
- `Docs/screenshots/` (home, currently, feed, profile at 390x844) generated from `seed_demo`. Settings and delete screens were shot at 390x844 and 1440x900 into the gitignored `.shots/` and checked by eye; I fixed section spacing and the missing bullets on the delete page after looking at them.
- `core/static/core/css/app.css`: settings and avatar styles only.
- Two earlier tests caught real slips in the first M6 commit when the full suite ran, and I changed the code, not the tests: `test_the_write_path_stays_single` forbids `EpisodeLog.objects` outside the tracking write path and selectors, so the export now reads episode scores through the new read-only `tracking.selectors.episode_logs_for`; `test_compose_runs_a_real_worker_inside_the_contract` requires the worker to mount every volume the app does, so the worker mounts `avatars` too (unused by it, commented in the compose file).

**Resource check** (compose stack from this branch, `docker stats` plus the containers' cgroup `memory.peak`, 2026-11-02). A synthetic 2,000-title MyAnimeList export (made up, not anyone's list) imported with all 2,000 library rows in about 100 seconds. Then: browsing Home, Currently, Library and a profile with 2,000 titles; downloading `library.csv`, `diary.csv` and `anime.xml` (each in under 0.4 s); re-importing the same file; exporting `anime.xml` and importing that. Both re-imports added nothing (2,000 rows `already_there`, 2,892 diary rows before and after).

| Service | Budget | Peak | Idle |
|---|---|---|---|
| app | 384 MB | 190 MB | 123 MB |
| worker | 256 MB | 94 MB | 60 MB |
| db | 384 MB | 102 MB | 37 MB |

Nothing is over budget, so nothing needed fixing. Caveats: the worker and database ran on a Docker network with no route out, so the metadata phase hit its failure path rather than real AniList or MAL (peaks cover the import's own streaming read, which is the heavy part, not a 33-minute metadata crawl); `docker stats` samples every couple of seconds, which is why the cgroup peaks are the numbers quoted; the box was x86, not the Pi, and the Pi's zram swap may change how it behaves near a limit. The worker container had restarted once at the very start (it came up before `migrate`, as `restart: unless-stopped` is meant to handle), before any import. `/currently/` is 646 KB of HTML with about 400 in-progress titles because it isn't paged: fine on this budget, worth paging after v1.

**Not done here, by design:** the restore drill on real data, going public, the Pi. Kyle's Cortex dossier for this project was not edited in this step (it lives in another repo with unrelated uncommitted changes); the nightly project scribe will see the drift. The `impeccable`, `emil-design-eng` and `web-design-guidelines` skills were not run as separate passes; `ui-pass` was, and the new screens reuse the app's existing form, menu and button vocabulary instead of inventing new components, with the phone numbers it sets (16 px inputs, 48 px fields and 44 px minimum targets, one column) checked on the 390 px shots.

**Why:** the plan's done criteria for M6 are numbers and a README a stranger can follow, so they are measured and written down rather than asserted.

### 2026-11-02: M6 release work: refresh job, export, settings, account deletion, hardening
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- **Daily refresh** (`catalogue/refresh.py`, tasks in `catalogue/tasks.py`, migration `catalogue/0004_refresh_flags`): at 04:37 `refresh_stale_titles` queues, per title, one job on that title's own source queue. Due means older than 150 days, or still airing and older than 7 days, or never fetched (an import stub whose details job was lost, i.e. owed for over a day). Airing first, then oldest first, up to `REFRESH_DAILY_LIMIT` (300) a day. A TV season is read with its series, not on its own. TMDB titles wait while there is no key, a MAL title goes to AniList while there is no client id, demo data is never touched. A failed refresh sets `refresh_failed_at` and `refresh_error` and changes nothing else (the row keeps everything, `fetched_at` stays old), and is not tried again for 3 days so one bad night can't eat later nights' allowance. Episode lists older than 150 days are re-requested, and `tidy` now queues a fresh download for each cached poster it drops at 150 days instead of waiting for a viewer. The Fribb sync was already weekly (daily check, weekly due) and is unchanged. `services.store_tmdb_show` was split out of `fetch_tmdb_show` so the refresh shares it.
- **`member` app** (`/settings/`): preferences (title language, adult toggle, default visibility), change password (current password, validators, throttled, ends every other session and keeps this one), avatar (PNG, JPEG or WebP up to 2 MB and 25 megapixels, re-encoded to a 256 px WebP with no metadata, stored as a random name in `AVATAR_DIR`, served only to signed-in members), the existing buddy picker, export, sign out and delete. Avatars show in the header, profile and people lists. The profile keeps its own sign out and visibility chips from M5 (their tests pin them), so those two exist in both places.
- **Export** (`member/export.py`): library, diary and episode scores as CSV (cells that start with `= + - @` get a leading quote so a spreadsheet never runs them) and anime and manga as MyAnimeList XML, all streamed in chunks of 500. The XML carries only titles with a MAL id and reads back through the M4 importer as a library it already has. For that, `imports/services._passes` now skips rewatch passes the library already has: before, a file saying "times watched: 2" about a title the member had logged twice by hand wrote a third pass, because only passes it had written itself had fingerprints. Not exported: posts, comments, CHUD history.
- **Account deletion** (`member/services.py`): password and typed username, throttled like login, the last active admin can't go. One transaction: open bounties on the member are refunded to their senders, names are rewritten to "Someone" in other members' CHUD ledger text, sessions end, then the user row goes and the cascades take everything the member owns. `chud.StickerGift.sender` is now nullable (`chud/0002`, safe on a live database): a sticker the member sent stays on the friend's post with no name, because the friend was paid and it is theirs. A sticker sent to the member goes with their posts and the sender is not refunded. Files (avatar, pending uploads) are removed after the commit, so a failure leaves the account whole.
- **Security pass** against plan section 7, with the `security-audit` ruleset as the checklist:
  - Settings fail closed: `DEBUG` is off unless `DEBUG=1`; `SECRET_KEY` has no fallback and is refused under 50 characters or starting `change-me` unless debugging; `ALLOWED_HOSTS` has no default and refuses `*`. `.env.example`, CI and the Dockerfile's throwaway collectstatic key were lengthened to match.
  - Headers (`core.middleware.SecurityHeadersMiddleware`): a Content-Security-Policy with no third party and no inline script (`style-src` allows inline style, because a few elements carry a computed width or colour), Permissions-Policy, `X-Robots-Tag: noindex`, and a public `/robots.txt`. HSTS for one year, this hostname only. `check --deploy` is clean; W005, W008 and W021 are silenced with the reason (no subdomains or preload on someone's real domain, and http to https is the tunnel's job because `/healthz` is probed over plain http).
  - Hand review of `tracking/views.py`, which M2's independent review never saw: `X-Episode-Rows` could make one request render 100,000 rows (now capped at 1,500); a malformed `HX-Current-URL` raised after the write was saved (500 on a saved write); scoring episode 99,999 and clearing it left an `Episode` row behind each time (now dropped when nothing hangs off it); `episode_score` with `skip` accepted any number (now 404 past `MAX_UNIT`).
  - M1's two notes: `everywhere_poll` and the search reuse now filter by owner (another member's query text and source errors were readable); the admin merge confirm carries a token of the pair as drawn, and `merge_media` turns a vanished row into a `MergeError` instead of a 500. `catalogue/tests/test_merge.py::test_admin_action_confirms_then_merges` had to send the new token, which is the only edit to an earlier test.
- **Infra and docs:** the `avatars` volume on the app service (production contract otherwise unchanged: services `app`, `worker`, `db`, `127.0.0.1:8990` only, `mem_limit` on all three), README rewritten for a stranger (install, every variable, backup and restore, deletion semantics), MIT `LICENSE`.

**Edits to the tests committed first, each because the first version was wrong, not to get green:** `test_refresh.py` read job args as a dict where `queued_jobs` returns JSON text; asserted the AniList host by its first label; and built the lost-stub case with a stub made a minute ago, which the "details job still in flight" rule (correctly) leaves alone, so it is now aged by two days. `test_security.py` used a 50 character key with one distinct letter, which Django's own W009 rejects. After a mutation check, these were made stricter: session rows must be gone (checked before Django prunes them lazily), a mid-deletion failure must also roll back an earlier bounty refund, preferences junk is tested per field, avatar pixel and format guards each get a case Pillow would otherwise accept, and the rewatch case now logs the second pass on a different day.

**Checked:** every new guard was weakened once and a test went red (60 mutations: refresh age, airing rule, order, cap, retry wait, flagging, season handling, key and demo rules, pending rule, flag clearing, poster and episode requeue; owner check, token, merge race; row cap, bad header, bare episode, skip range; password, username, throttle, last admin, bounty refund, name scrub, sessions, gift sender, avatar file, rollback; password current, throttle, validators, sessions, preference choices; avatar size, pixels, format, name, re-encode, old file, cache; CSV guard, own rows, XML characters, no-store, rewatch passes; key, hosts, HSTS, CSP, robots, debug default).

**Not verified / left:** the MAL XML field list is from memory of MAL's own export, not checked against a real one. A possible lock-order inversion between `merge_media` (row locks, then per-title advisory locks) and a member write (advisory lock, then the row's key-share lock) was read but not reproduced. `episodes_screen` is a GET that may queue a fetch (deduped, low risk). Avatars are not in the export.

**Why:** M6 is the release milestone. The brief asks for a data lifecycle a stranger can trust (re-read, export, leave), the security checklist actually run, and the unreviewed file reviewed by hand.

### 2026-11-02: Add the M6 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Tests only, and they fail at this commit on purpose.
- `catalogue/tests/test_refresh.py`: the daily metadata refresh (what is due, airing first, the daily cap, queues per source, failure flags, episodes and posters).
- `member/tests/`: a new `member` app for the settings screen, data export and account deletion. `test_export.py` (CSV and MAL XML, and export then import adding nothing), `test_delete.py`, `test_settings.py`, `test_avatar.py`.
- `core/tests/test_security.py`: the plan's section 7 as tests (settings that fail closed, cookies, HSTS, CSP and other headers, robots.txt, every route needing a login).
- `catalogue/tests/test_hardening.py` and `tracking/tests/test_hardening.py`: the findings of the hand review of `tracking/views.py` that M2's independent review never saw, plus the two M1 notes (`everywhere_poll` had no owner check, `merge_selected` no staleness check).

**Why:** M6 is a release step, so the done criteria (export round-trips, deletion is tested, the refresh keeps a failed row, nothing leaks) go in first and the implementation is held to them.

### 2026-11-02: TMDB fills Home's popular movies and TV through the daily job
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- `catalogue/upstream/tmdb.py`: `Tmdb.popular(kind, limit)` reads `/movie/popular` or `/tv/popular` and returns the same `Item` rows a search hit uses, paging (TMDB gives 20 a page) until `limit`, without repeats.
- `catalogue/popular.py`: `refresh()` now loops over sources (`SOURCES`: TMDB for movie and TV, MAL for anime and manga) and runs one shared per-kind routine, so every kind gets the same rules: a failed kind keeps its old set, an empty answer wipes nothing, rows are upserted by `(media_type, external_id)` so a tile keeps its pk, dropped titles go `listed=False` and are purged after seven days, posters are registered. `refresh(source=...)` does one source. A source with no key is skipped outright, and its kinds keep what they had. `enabled()` is the flag plus at least one configured key (`configured_sources()`).
- `catalogue/tasks.py`: the 05:23 job queues one task per configured source: `catalogue.refresh_popular` (unchanged name, MAL queue) and the new `catalogue.refresh_popular_tmdb` (TMDB queue). Each keeps its own queue, lock, pacing and queueing lock (`popular-mal`, `popular-tmdb`).
- `catalogue/services.py`: `open_item(item)` is `open_hit` without the hit, so a popular TV tile creates the Show exactly the way a TMDB search hit does. `popular.open_tile` uses it, and `open_popular` redirects to the show page for a Show.
- `core/views.py`: Popular movies and Popular TV read the cache first and fall back to local data, with the same adult filter as anime and manga. Home still makes no upstream call. `popular.for_home(user, limit)` now returns every kind's tiles from one query instead of one per carousel, which keeps Home inside the existing query budget (`test_home_query_count_does_not_grow_with_titles`) now that four carousels read the cache, not two.
- `.env.example` and `README.md`: `POPULAR_TITLES_JOB` now covers movies and TV too, and says which key each source needs.

**Decisions:**
- **TV in `PopularTitle`:** `media_type=tv`, `namespace=tv`, `source=tmdb`. `MediaType` already had `tv`, so no model change and no migration. `0003_popular_titles` is on `build/v1` but not on origin/main either way, and nothing here touches it.
- **Adult:** TMDB's docs describe both list endpoints as discover calls with `include_adult=false`, and neither takes the parameter, so there is nothing to send and adult titles are not asked for. The movie list still carries `adult` per row, which is kept as sent so Home's filter works if one ever comes back. The TV list has no such field, so its rows are `is_adult=False`; that is what the list returned, not a check of each show. This rests on the docs, not on a live call: not verified against the real API, because no key was used.
- **Per source rather than one job:** one job calling both clients would hold a TMDB or MAL slot while it waited on the other, and would break the rule that each source's calls go through its own queue and lock.
- **A second page failing fails the kind:** the old set stays rather than a half-new one.

**Why:** Shahan found Home's Popular movies and Popular TV nearly empty on a fresh site, because they only read local data. His UI doc has TMDB supplying them through the same daily `popular_titles` job, behind the same off-by-default switch, so that is what this builds. Dev and tests stay on recorded lists (`tmdb_movie_popular.json`, `tmdb_tv_popular.json`).

**Checked:** the tests were committed first (28 red), then green. The only change to the committed tests was adding a "no refresh failed warning" assertion to the two one-source tests, because weakening the skip-a-source guard left them green (the client also refuses without a key); that was a strengthening, not a way to get green. Each guard was weakened once and its test went red: empty answer, a failed kind, unlisting dropped titles, the seven day purge, skipping a source with no key, `enabled()` needing any key, the adult filter, TV opening as a Show, paging dedupe, stopping on a short page, the cut at the limit, the adult flag being kept, one job per source, and Home reading the cache for movies and for TV.

### 2026-11-02: Add the tests for TMDB popular movies and TV before the change
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/tests/test_popular_tmdb.py` and two recorded TMDB popular lists (`tmdb_movie_popular.json`, `tmdb_tv_popular.json`). They pin: the client reading `/movie/popular` and `/tv/popular` (and paging past TMDB's 20 per page), adult titles never asked for and the flag kept as TMDB sent it, `enabled()` for the flag and either key, one queued job per configured source, a refresh that fills movies and TV, keeps a failed kind's old rows, never wipes on an empty answer, unlists a dropped title and purges it after a week, makes no call to a source with no key, opening a popular movie and a popular TV tile (the TV one makes a Show, as a search hit does), and Home reading the cache first with no upstream call and falling back to local data. They fail at this commit on purpose.

**Why:** Shahan's UI doc has TMDB supplying Home's popular movies and TV through the same daily job as anime and manga, and they are nearly empty on a fresh site today. The acceptance tests go in first so the change has something to be held to.

### 2026-11-02: An on hold title resumes when its next episode is logged
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `tracking/services.py`. Logging an episode, chapter or season row by hand on an on hold title clears `user_status` and `status_set_on` and closes the open `HoldSpell` as of the log's date, in the same transaction and under the same lock as the write. The status then derives as usual: In Progress, or Completed if that log finishes the title. This lives in `_resume`, the write path, and `derive` stays a pure calculation; its "On hold and dropped stay" comment now says why they stay there and where they are lifted. `tracking/runstats.py` needed no change: the spell's end date is the day the title came back, so the hold days are the days before it and the log day counts as a day spent watching (a spell from the 25th to the 29th holds four days; tests pin this for the run and the CHUD pace).

**Edge calls, each Shahan's to overrule:**
- A backfilled row dated before the hold started does not resume the title. It is a record of something watched earlier, not the member picking the show back up. A row dated on the day the hold began does resume, with a spell of zero days.
- An import does not resume a title. Imports already passed `keep_status`; `add_diary_row` now also ignores any row whose source is not "Logged here", so a caller that forgets the flag can not resume by accident.
- Removing the log later does not put the title back on hold. The member took it off hold by logging, and undoing a log is not a decision to hold it again. The spell stays closed.
- Resuming does not open the Post or Skip prompt. The prompt is raised by the title finishing or by the member choosing hold or drop, and a resume is neither.

**One thing in the brief that did not match the code:** it said logging on a dropped title leaves it dropped today. It does not: M2's `_resume` clears dropped as well as on hold, and `test_logging_takes_a_title_off_hold_and_off_the_watchlist` pins that. The brief also put changes to dropped out of scope, so dropped behaves exactly as before (any hand log takes it to In Progress, no date check, imports leave it alone) and `test_dropped_follows_its_own_rule_whatever_the_date` pins that. If Shahan wants a dropped title to stay dropped when logged, it is one condition in `_resume`, but it changes what M2 built and the Library's Dropped filter.

**Why:** Shahan's decision is that there is no resume button: logging is the resume. The mechanism existed but resumed on any dated row, including a backfill from before the hold, and on an import row from a caller that did not pass `keep_status`. Both made the hold spell, and so the run stats, wrong.

**Checked:** the tests were committed first (6 red), then green. Each guard was weakened once and its test went red: the date check (`test_a_backfilled_row_dated_before_the_hold_does_not_resume`), the import source check (`test_an_import_does_not_resume_a_title[mal-False]`, `[letterboxd-False]`), limiting the date check to on hold (`test_dropped_follows_its_own_rule_whatever_the_date`), closing the spell, clearing the status, and closing the spell on today rather than the log date. "Removal does not re-hold" and "no prompt" have no guard of their own to weaken: they follow from the status being cleared and from the prompt only being raised on completion, so they pin the behaviour against a later change rather than a line of code.

### 2026-11-02: Add the tests for on hold titles resuming before the change
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `tracking/tests/test_resume.py`. An on hold title goes back to In Progress when the next episode or chapter is logged by hand (+1, Log several, a hand-added row), or to Completed if that log finishes it. The hold spell closes on the log's date and the run stats leave out exactly the held days. Not resumed: a row dated before the hold started, any import row. Taking the log back later does not re-hold. Resuming raises no Post or Skip prompt. Dropped and planned are pinned as they are. Six of them fail at this commit on purpose.

**Why:** Shahan's decision is that there is no resume button: logging is the resume. `_resume` already took a title off hold on any hand log, so most of this passes today. What fails is the part that was never decided in code: a backfill dated before the hold, and an import row that does not pass `keep_status`.

### 2026-11-02: Read every upload in a child process under a memory ceiling
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- **The net.** A file is now parsed by `imports/child.py`, a separate process whose address space is capped at what it starts with plus 96 MB (`IMPORT_CHILD_MEMORY_MB`, `RLIMIT_AS`) and which is stopped after 15 minutes (`IMPORT_CHILD_SECONDS`). It sends rows to the worker over a pipe, one JSON object a line, and the worker stores them as it reads them. Whatever a crafted file finds inside expat, `csv` or `zipfile`, it is the child that runs out, not the worker with its 256 MB. The child imports only the parsers (no Django models, no database) so it starts in a fraction of a second, and the worker's own connections are never touched. The limits in `bounded.py` stay as the first line of defence.
- **What the job does about it.** A file the child refuses fails the job with its message, as before. A child that reaches its ceiling reports it (a `MemoryError`, or expat's "out of memory", which arrives as a SAX error and is now recognised as one) and the job fails at once with a plain message and its attempts at the cap, since the same file would reach it again. A child that is killed, crashes, exits without an answer or runs too long is tried again, counted in `attempts`, and the job fails with a plain message at the cap. A child that dies once and then works finishes normally, and a clean finish clears the count. Nothing loops, and the upload and any stored rows go with a failed job.
- **Headroom.** The biggest export the importer accepts (50,000 films) needs about 32 MB of headroom in the child, so 96 MB is three times that. A worker of about 65 MB plus a child of a base interpreter and 96 MB stays near 200 MB. Where `/proc/self/statm` does not exist the ceiling is skipped, so a dev machine that is not Linux still runs.
- **Three more ways in, fixed at the root.** A zip64 locator before the end record makes `zipfile` take its counts from a zip64 record whatever the classic one says, which got past the directory check: a 15 MB crafted zip made `zipfile` build 300,000 entries and grew the process by 117 MB. The check now looks in the same place `zipfile` does and refuses any zip64 locator. A CSV record whose every line ended inside a quote never ended, so `csv` kept a field per line: records are now counted by `bounded_rows` and held to 8 lines and 32 KB. The old `csv.DictReader` is replaced by it, with the same blank-row and missing-field behaviour. The XML guard counts distinct element names and refuses more than 256, because expat keeps every one it meets, and a real export has about forty.
- Existing test changed: the 20,000-line quoted field is now refused by the record guard before `csv`'s own limit, so it expects "spread over too many lines".

**Why:** the reviewer found a different internal each round. The net is the only fix that does not depend on predicting the next one, and the caps stay because a clean refusal beats a killed child for the member.

**Checked:** the new tests were committed first and failed. The one thing weakened afterwards was the ceiling (`setrlimit` removed): the child test and the job test go red. Peak memory for each crafted input is measured in a fresh process, as before, and stays under 60 MB. The child's cost is not in those numbers, since it is a separate process. The suite was not re-run in full until the end of this round.

**Still unbounded:** the child's own pipe output is read a line at a time with a 1 MB cap per line, but the number of rows is not capped by the pipe, only by the 50,000 films or the file size, and each row is stored as it arrives. The XML entries a file may hold are limited by its inflated size (200 MB) and nothing else. The ceiling is on address space, not on CPU: a file is stopped after 15 minutes, not before. And a process-level limit is only as good as the platform's: on a host without `RLIMIT_AS` the child runs without one and the bounds in `bounded.py` are all there is.

### 2026-11-02: Add the tests for the fifth M4 review round before the fixes
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Tests for the three new findings and for a process-level ceiling under all of them. The three: a zip64 record sitting in front of a classic end record that looks harmless (a crafted 15 MB zip whose directory `zipfile` reads as 300,000 entries, growing the process by 117 MB), one CSV record whose fields each end a line inside quotes, so it never ends and `csv` keeps a field for every line, and an XML file of millions of distinct element names. The ceiling: a parse that needs more memory than the child is given fails the job once with a plain message, a child that is killed is tried again only up to the attempt cap and then fails the job, a child that dies once and then works is not held against it, a child that exits without finishing counts as a failure, and a child that runs too long is stopped. They fail at this commit on purpose.

**Why:** Each round the reviewer found another way for a small upload to grow memory inside expat, `csv` or `zipfile`. Closing them one at a time cannot end, so the tests also pin the net: whatever the next one is, the thing that runs out of memory is a child process, not the worker.

### 2026-11-02: Close the class: one bounded-input layer under both import readers
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `imports/bounded.py` is the one place the limits live, and `parsers.py` sits on it. The previous rounds fixed one hole each (a tree that kept every element, a screen that missed end tags, a zip read whole into memory), and the reviewer found the next each time. This is the same fix at the level of the class.
- **Bytes.** `BoundedReader` charges every byte that comes out of a decompressor to a `Budget` and raises past it. The XML reader has one for the whole file, and each zip member has one of its own (its size limit, or a ratio of its compressed size, whichever is less) plus one shared by the whole zip. Nothing downstream can be handed more than the budget, wherever it buffers it.
- **Tokens.** `XmlGuard` follows the bytes on their way to expat and tracks the running size of the token it is in: a tag (256 bytes, and only a name, so an attribute is impossible and nothing can hide a value in a start tag), a comment (4 KB), CDATA and a text node (1 MB each). The old screen only looked at start tags, so `</` followed by 300 MB of name, or `</a` followed by 300 MB of spaces, was buffered whole by expat: with the old code the first grew the process by 514 MB and the second was read as if it were fine. Text and CDATA caps are new, and no real field is near them. `bounded_lines` reads a CSV one line at a time with a cap of 64 KB before `csv` sees it, and `csv`'s own field limit holds a quoted field spread over many short lines.
- **Containers.** `check_zip_directory` reads the end-of-central-directory record itself, before `zipfile` is allowed to build anything: more than 200 entries, a directory over 256 KB, or any zip64 marker is refused. The headers are then checked as before, and now also refuse any method other than stored or deflated (LZMA and bzip2 allocate a dictionary the header chooses), and a compressed total over the upload limit.
- Every refusal is an `ImportRejected` with a sentence for the member, which fails the job and nothing else. `ImportRejected` moved to `bounded.py` and is re-exported from `parsers`.

**Tests:** `imports/tests/test_bounds.py` runs every crafted shape in a fresh process and asserts both a plain refusal and peak memory under 60 MB (80 for the honest 40,000-film zip): 13 XML token shapes at 300 MB each, a file of nothing but open tags, 300 MB of ordinary elements read in flat memory, the XML total budget, five forged end records, a missing end record, LZMA and bzip2 members, 201 entries, 450,000 distinct films, a 25 MB single line, a quoted field over 20,000 lines, a ratio bomb, three files held to the zip total, and the honest zip. Against the previous head, 14 of those fail. The old memory tests in `test_parsers.py` moved here, except that a single huge text node and a huge CDATA are now refused, not read.

**Checked:** the tests were written after the layer this time, not before, so I ran them against the previous head instead: 14 fail there, including `</` plus 300 MB of name (the process grew 514 MB) and `</a` plus 300 MB of spaces (read without complaint), a 25 MB line, five forged end records and the LZMA and bzip2 members. Then each cap was weakened once and seen red: the byte budget and its charging, the text, tag and comment caps, the tag shape (an attribute), the declaration cap, the line cap, the directory entry count, size and zip64 checks, reading the directory before `zipfile`, the packing methods, the compressed total, the film cap, line bounding before `csv`, and the XML guard and its final flush. Two pairs are layered and go red only together: the zip total on the headers against the zip total on what comes out, and (from the round before) the entry size likewise.

**Still unbounded, or only bounded by something else:** the gzip's own compressed bytes are bounded by the upload cap (25 MB), not by a budget in this layer. The films kept while joining are capped at 50,000 (about 35 MB), and the rows applied later are capped at 50,000 by the job. A text node under 1 MB is not charged beyond the byte budget, which is deliberate: expat hands it over as it arrives.

### 2026-11-02: Fix what the third independent read of M4 found
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- **MAL's own export is read again.** Its real file opens with an XML declaration and a comment naming the exporter, and the markup screen I added last round refused any comment, so a real export would have been rejected whole. The screen now allows a comment of up to 4,096 bytes (counted across reads), and still refuses a longer one, one that never ends, a DOCTYPE, a processing instruction, an attribute and a long tag name, all of which expat would buffer whole. The first few hundred bytes are waited for however the file is sliced, so the declaration is judged whole. A test starts a fixture with MAL's header, plain and gzipped, and the import runs end to end on one.
- **A Watching entry with nothing watched is skipped on a title the catalogue already has, too.** Last round's fix only covered titles the import had to make. For a title already in the catalogue the row said "already in your library" with no row and no entry, which is false for this member. It is now skipped with the same reason whenever the member ends up with no entry, and "already there" is kept for a member who really does have it.
- **The Letterboxd zip is streamed.** Each CSV goes through a decoder and the CSV reader a slice at a time, instead of being read whole into memory, decoded and parsed. Films are held to 50,000 and watch dates to 200 a film while reading (the old check came after the whole list was built), and the compression ratio is limited to 100 to 1, checked on the headers and again on what actually comes out. The new setting is `IMPORT_ZIP_MAX_RATIO`. A crafted 8 MB zip of 450,000 different films (27 MB inside, a ratio of 3, so under every size limit) grew the process by 411 MB with the old reader and by 30 MB with the new, which refuses it. An honest 40,000-film zip is read in under 80 MB (the test limit) and a zip that squashes thousands to one is refused.

**Why:** the reviewer was right on all three. The first broke the importer's main purpose on a real file, the second made a summary say something untrue, and the third was the same kind of unbounded read as the XML one, one layer over. Dropping the budget that was meant to hold the zip's total as it was read: `zipfile` never returns more than a header claims, so the headers hold the total and a counter would be dead code.

**Checked:** guards weakened once each and seen red: the comment cap and where it is checked, the header comment being allowed, the film and date caps, streaming (a list of rows instead), both ratio layers together, the declared total, both entry-size layers together, and the skip for a catalogue title. Some guards are layered, and each alone survives because the other covers it, by design: the ratio on the headers against the ratio on what comes out, and the declared entry size against the counted one. Only weakened together do they go red. The three older zip size tests now set the ratio limit out of the way, so they test the size limits they were written for, and one test file's diary dates were too few distinct ones to reach the cap and now use real dates. Memory is measured by `ru_maxrss` in a fresh process.

### 2026-11-02: Add the tests for the third M4 review round before the fixes
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Tests for the three findings: an export that begins the way MAL's own does (an XML declaration, then a comment naming the exporter) is read, while a comment that goes on, never ends or hides an entry is not mishandled; a 0-progress Watching entry on a title the catalogue already has is skipped, and the same entry for a title the member already has is "already there"; and a Letterboxd zip is read as a stream, with a ratio limit that counts what actually comes out, a cap on films while reading, a cap on dates per film, and peak memory measured in a fresh process on a crafted zip of 600,000 films and on a big honest one. They fail at this commit on purpose. The three older zip size tests now set the ratio limit out of the way, so they stay about the size limits they were written for.

**Why:** The screen I added last round refused MAL's real header, so the importer's whole point failed on a real file. The zip reader still held every member whole and built a dict per film before any row limit applied.

### 2026-11-02: Fix what the second independent read of M4 found
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- **Nothing to add is skipped, not "added".** A Watching or Reading entry with nothing watched made a title and no library row, and still counted as added. The row now ends skipped, with a reason, and the title it would have made is never made (the row's transaction is undone), so there is no orphan to ask AniList about. With a score it still gets its row. Whether a row was "added" is now decided by what happened, not by whether the title had to be made.
- **Plan to Watch and Plan to Read keep their tags and comments.** The notes and tags merge ran only for the other statuses.
- **A chunk of MAL rows is one transaction, with its request for details inside it.** A worker killed part way loses the whole chunk, and the retry redoes all of it, request included. A chunk that finished is never asked for twice, because the request commits with it. Letterboxd chunks stay per row, because holding a transaction across TMDB calls would hold members' title locks for minutes, and they make no titles to ask about.
- **The MAL reader is a SAX reader with a screen in front of it.** The old one built a tree and kept every non-entry element, so a 300 KB upload that inflated to 300 MB took the process to 300 MB more (measured: `ru_maxrss` grew 301 MB for one huge text node, 299 MB for many elements). Now only the importer's own fields are kept, each cut to 2,100 characters as it arrives (including when it comes as millions of character references), and nesting past six levels is refused. Expat reports a comment, a DOCTYPE, a processing instruction, an attribute or a tag name only once it has all of it, and the same 300 MB in one of those grew the process by 512 MB, 916 MB for an attribute. A byte-level screen therefore refuses those before expat sees them: MAL's export has none (it uses CDATA for text, which is read as it arrives and may hold anything, including markup, so the screen tracks it). The same six shapes now grow the process by 0 MB, or are refused.
- **Retries are counted, in the database.** `ImportJob.in_flight` is set when a worker starts a step and cleared when it finishes one. A start that finds it still set is a retry after a kill, and `attempts` counts those. After three the job fails with "That import kept crashing the worker", its upload is deleted, and what it had added stays. A clean finish clears the count, so one unlucky kill does not add up across steps. Retrying no longer resets the stuck timer's only evidence. Both columns are folded into `imports.0001`, which has not landed.
- **`imports.recover` no longer lets one bad retry stop the sweep.** A stalled job whose twin is already queued (the same queueing lock) cannot be retried, and left in "doing" would hold the shared lock. It is now closed instead, checked first, and any other failure to retry is logged and the sweep goes on to close stuck imports.
- **An import-side test that imports collect no bounty,** which this log said was covered and was only covered in `chud`. It places a bounty, imports the title as completed, and checks the bounty is still open and no points moved.

**Why:** the reviewer was right on all four. Each was a way to lose data (the dropped tags and the lost request), mislead the member (the count) or take the worker down (the memory), and the memory one only mattered because the worker has 256 MB.

**Checked:** guards weakened once each and seen red: the skip, the added count, planned notes, the chunk transaction, the attempts increment and cap, the in-flight flag, the clean-finish reset, the twin check, the markup screen (and its final flush and its tail hold-back), the field cap (and its guard while collecting, found only once a test fed millions of character references), the nesting cap, the depth of an entry, bounty collection and points. Tests that were too weak at first and are fixed: nesting (an empty file was rejected for another reason), and the memory test used a stream that cannot seek, so the reader no longer seeks. Memory is measured in a fresh process by `ru_maxrss` in the tests, which are noisy by tens of MB, so each shape is large enough that a failure is far over the limit.

### 2026-11-02: Add the tests for the second M4 review round before the fixes
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Tests for the four findings and two extras from the second independent read: a Watching or Reading entry with nothing watched is skipped, not counted as added, and leaves no title behind; Plan to Watch and Plan to Read keep their tags and comments; a chunk cut short loses neither its rows nor its request for details, and a re-run does not ask twice; a job whose worker keeps dying is failed after a few tries with a clear message; a file that inflates to hundreds of megabytes (one huge text node, many non-entry elements, one huge field in an entry) grows a fresh process by under 60 MB, measured by `ru_maxrss`; a stalled job whose twin is already queued does not stop the sweep; and an import collects no bounty. They fail at this commit on purpose.

**Why:** Each finding was a real way for an import to lose data, wedge the queue or take the worker down, and the memory one needs a number, not a reading of the code.

### 2026-11-02: Fix what the independent read of M4 found
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- A re-import no longer puts On-Hold or Dropped back on a title. It now applies those only to an entry the import itself is making, read before any rows are written. A blank `user_status` on an existing entry can be the member's own doing, because logging resumes a title, so it is no evidence that nobody set one. Tests: import On-Hold, log the next episode, import again, and the title stays in progress and counts as already there. Same for a title finished here against a Dropped file.
- A worker killed part way no longer leaves an import, or the queue, stuck. `ImportJob` gains `heartbeat_at`, touched after every row (folded into `imports.0001`, which has not landed). A new periodic task `imports.recover` (every five minutes, on `maintenance` so the shared `imports` lock cannot block it) retries Procrastinate jobs stalled in the `imports` queue, using the worker heartbeats it already keeps, then closes any running import that has not moved in an hour and says why, so the member can upload again. Reading a file is restartable: a job still holding its upload starts again from nothing, one whose upload was already read goes straight on to applying, and the database now forgets the upload before the file is unlinked, so a kill between the two cannot leave a job pointing at a missing file.
- The route is `imports:index`, not `imports:home`. `core.context_processors.shell` takes the active tab from the bare route name, so `/import/` lit the Home tab. A test holds that the import page names no tab and that Home still does.

**Why:** the reviewer was right on all three. The first broke "never overwrites a user-set status", the second made one OOM kill or deploy during an import block every member's imports with no way out short of editing the database, and the third told sighted and screen reader users they were on Home. Only the `imports` queue is retried here. The same stall exists for the other queues, which is not this step's to change.

**Checked:** guards weakened once each and seen red: the entry-is-new condition, the one-hour close, the restart of a partly read file, the straight-on branch, the stalled retry, the heartbeat test (a live worker's job is left alone) and the route name. Full suite, Ruff and migration checks were run again.

### 2026-11-02: M4 imports: MAL XML and Letterboxd zip, progress, review, fingerprints
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `imports` app: `ImportJob` and `ImportRow` (`imports.0001`, two new tables, so safe on the v0.0.1 database), `parsers.py` (the two readers and their limits), `matching.py` (Letterboxd to TMDB), `services.py` (uploads, reading a file into rows, applying rows, review, retry, the purge), `tasks.py` (queue `imports`, plus a daily `imports.purge_old`), and the screens at `/import/` (idle, running with HTMX polling, done with counts, and a review page). A link sits in the profile menu.
- MAL: `defusedxml` streams the file one entry at a time (DTDs, entities and external files refused), a gzip is counted as it inflates (200 MB cap), exact match by MAL id, status words and codes mapped, score 0 or off the scale becomes unrated, dates, tags, notes, rewatches (times watched become full passes), manga chapters and volumes. Rows are made from the file alone (`catalogue.services.get_or_create_stub`), so the library fills at once. Details then fill in: new titles go to a new `catalogue.anilist_batch_details` task 50 at a time (AniList's `idMal_in`, which the M1 spike proved works), and anything AniList lacks falls back to the MAL API one a second, or to AniList by id with no MAL client id.
- Letterboxd: the zip is checked before anything is read (entry count 200, 30 MB an entry, 100 MB in all, unsafe names, passwords, then counted again as it inflates) and `watched`, `ratings`, `diary` and `watchlist` are joined by title and year. `Tmdb.search_movies` finds candidates. Only an exact normalised title, an exact year and exactly one such candidate is accepted unasked. Everything else, including two exact matches, goes to review. A film that maps to a MAL id attaches to that anime row, making it if there is exactly one such id, and staying a film for an admin to merge if there are several. The Letterboxd address is kept as a secondary id, so a re-import does not search again for films it already knows.
- Re-import: every diary row has a fingerprint (unique per member), MAL writes only the ranges the diary does not already cover, and a score or status the member set (and notes, and tags already there) is never overwritten. Imports write through `tracking.add_diary_row` with their own `source`, so `chud/receivers.py` already ignores them: no points, no XP, no bounties collected, no posts. Tests hold all four.
- Privacy: an upload is saved under a name of our own with mode 0600 and deleted as soon as it has been read, or failed. `import_rows.raw_data` is cleared 30 days after a job finishes, and stray uploads after a day, by the daily job.
- Existing files touched: `catalogue/services.py` (stub, batch fetch), `catalogue/tasks.py`, `catalogue/upstream/tmdb.py`, `tracking/services.py` (`covered` and `lock`, public names for what imports need), `config/settings.py`, `config/urls.py`, `requirements.txt` (`defusedxml`), `docker-compose.yml` (queue `imports`, six slots, an `imports` volume shared by app and worker), `.env.example`, `README.md`, the profile template and `app.css`.
- Test changes after the acceptance commit, none loosening what is checked: `catalogue/tests/test_worker.py` asserted that the worker's queues are those of `catalogue.` tasks, and now counts `imports.` tasks too, since the worker must cover that queue as well. In the new tests, a count of three diary rows was my arithmetic (the watchlist film has none, so two), the shared fixture gave every rating the same address, and one test read a row it had not refreshed.

**Why, including what I had to decide:**
- **AniList first for the backfill.** MAL's API is one request a second, so 2,000 titles take over 33 minutes. AniList's batch does the same in about 40 requests, and the plan allowed it if the spike held. Titles it lacks go the slow way, so nothing is lost. The cost: a title filled this way has `metadata_source` anilist, not mal, and no refresh job upgrades it until M6.
- **The job's counts are read from its rows, not stored,** so they cannot disagree with what happened. The design doc's `processed_rows` and the others are therefore queries, not columns, and `candidate_media_ids` is a JSON list of candidates carrying their external ids, as the plan says.
- **Row status stays as the design doc has it** (auto, needs_review, confirmed, skipped, failed, with pending added), and what a row came to is a second column, `outcome` (added or already there).
- **Dates.** The brief says imports create undated rows, but MAL's start and finish dates are real data. A MAL entry with dates is written as its first episode on the start date and the rest on the finish date, so the library groups it by month and the stats slide has something. With no dates a row is undated and falls in the No date group. A date in the future is dropped.
- **Letterboxd dates are one row per diary watch,** so a rewatch is a rewatch. A watched film with no diary date is one undated row, and a film already logged here on that day, or at all if undated, is not logged again.
- **Not verified:** the Letterboxd export's file and column names are from its documentation, not a real export, and diary URIs are treated as the log's, not the film's. Shahan can try a real private export, and the matching rule is meant to be tuned against it. The MAL sample was a small made-up list with real public ids, run end to end against the real AniList.
- **One import of a kind at a time per member,** by a partial unique constraint, so a double submit starts one. Review answers lock the row, and the job closes under its own row lock, because the last answer and the worker finishing can land together.
- **Limits sit in the view and the parser.** The view refuses a declared length and a file over 25 MB before keeping it, but Django has already streamed the body to a temp file by then, so the real bounds are the parser's, and a reverse proxy should cap uploads too.

**Checked:** 54 guards weakened once each in a copy of the repo, then four more variants (`~/.cache/mediatracker/scripts/mutate_m4.py`, not committed), including the XML entity and DTD flags, both XML and zip inflate limits, every traversal form, entry count, passwords, upload size, declared length and first bytes, the owner checks, the choice bounds, double confirm, the settle lock, never overwriting a score or status or notes, only-new ranges, the exact title and year rules, the purge, the one-at-a-time constraint, HTML escaping and the merge rule. Eleven survived the first time. Two were dead code I removed (a second root check and a zip magic check that `zipfile` repeats), five gaps got their own tests (drive letters, a watchlist over a dropped title, notes, a film logged here the same day, a film fitting several anime), one was weakening the model while the migration still held the constraint, and one needed a file that breaks after more than 500 entries. The three XML flags and the two zip size layers each cover for the other: weakened together they go red, weakened singly they do not, by design. Also run for real: a worker and the app against a throwaway Postgres, a small sample MAL file uploaded in the browser at 390x844 (reading, 7 added, details filled in from AniList), the same file again (7 already there, no new diary row), the review page answered with htmx, and 1440x900 shots. Screenshots are in `.shots/` (not committed). The Letterboxd path ran in tests only, because this machine has no TMDB key.

**For the PR description, where the docs and prototype differ:**
- The prototype says details fill in "at 60 requests a minute". That was Jikan. Here it is AniList in batches first, then MAL at one a second, and the page shows a count and an upper bound.
- The prototype's review rows are inline on the import screen. Here they are a page of their own (twenty at a time), linked from the Letterboxd card, because a real export may have hundreds.
- The prototype's import buttons are "Use sample export". Here they are real file pickers.
- Design doc: `import_jobs` counts are queries, `candidate_media_ids` is JSON candidates, and `import_rows` has an `outcome` column.
- Brief: imports create undated rows. MAL rows carry its dates when it has them.
- Deploy note: the compose file gains an `imports` volume and a sixth queue, so the deployed compose file needs the same.

### 2026-11-02: Add the M4 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `imports/tests/`: the two readers (what a good MAL export and Letterboxd zip say, and what they refuse: malformed XML, entity expansion, external entities, a gzip bomb, a zip bomb, a lying zip header, path traversal, too many entries, encrypted entries), the MAL import from upload to library rows to details filling in behind, the Letterboxd import through matching and the review screen, idempotency in both, the screens (idle, running, done, review, ownership, CSRF, upload checks) and the purge. The exports are built in the tests from made-up titles and ids, so there is no personal data and no fixture file. None of the code exists yet, so they fail at this commit on purpose.

**Why:** The step's done criteria are the tests: a sample of each export imports end to end, importing twice adds nothing, and every guard is shown to fail when weakened. Writing them first fixes what "imports earn nothing", "never overwrites a score or a status" and "add only what is new" mean before there is code to bend them to.

### 2026-11-02: The CHUD layer: XP, points, buddies, stickers, the store, gifts, bounties and Chud of the Week
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `chud` app. `rules.py` holds the sum, the levels and the sticker and buddy catalogues with no database, ported from the prototype. `ChudAccount` holds stored balances and is the row every spend locks. `ChudLedger` is append-only, one signed row per change. Also `UserSticker`, `StickerGift`, `Bounty` and `WeeklyChudWinner`. `accounts.User` gains `chud_buddy`, as the plan says (`accounts.0002`). All new tables or one blank column, so safe on the v0.0.1 database.
- `tracking/signals.py`: `entry_logged` and `entry_unlogged` now also carry `event`, `first` and `row`, and a new `entry_recomputed` fires when an entry is brought into line with the diary. `tracking/runstats.py` gains `pace_for`, the multiplier's reading of the same run the stats slide uses. `_recompute` is split in two so the signal fires on every way out of it.
- Earning: `amount = max(1, round(hours * 10 * (1 + chud / 100)))`, on the latest pass, with days on hold left out, as `earnPatch` does. A movie is its own one-day run, which gives the prototype's +27 for two hours.
- Screens: the Profile section, the store at `/chud/store/`, the gift sheet on posts and comments, stickers grouped under them, the level-up sheet, a bounty sheet on the title page and a Bounties section on your own profile. `chud/middleware.py` adds what a write earned to the answer's `HX-Trigger`, so `tracking` never hears of it. `seed_demo --library-for X` now gives the prototype's balance, and `--million-xp` its 1,000,000 XP. Neither is reachable from production code paths. `manage.py verify_chud [--repair]`, read-only admin views of the ledger and the other tables.
- A daily job (`chud.decide_chud_of_the_week`, on the existing `maintenance` queue) decides the last whole week if it hasn't been. Daily, so a machine that was off on Monday still catches up.
- Touched: `social/` (`stickers.py` now reads the gifts, `selectors.comments_for` returns a list with each comment's stickers, the gift and sticker slots, `_profile_chud_slot.html` replaced by `chud/_profile.html`), `core` (sheet block, toast popover, two icons), `tracking/_title_actions.html`, `seed_demo`, `README.md`.

**Why, including every rule I had to interpret:**
- **A negative balance is Shahan's call, 2026-11-02, reversing the brief's "points never go negative".** Removing a log takes back exactly what it earned, even past zero if it was spent. While the balance is not positive nothing can be spent, whatever the price, through one check (`services._check_can_spend`) that every debit goes through. Sending a sticker you already own isn't spending, so it stays allowed, and refunds and gifts received still land and can bring it back up. The first build parked the shortfall as `debt`, which is gone, along with its column and the `chud_points_not_negative` and `chud_debt_not_negative` constraints, folded into the unlanded `chud/migrations/0001_chud.py`. Only the XP constraint stays. The store, gift sheet and bounty sheet show the real balance and say why spending is blocked.
- **XP has a floor, and I added it here.** Kyle's message asks to keep the "current clamp", but there wasn't one: a removal subtracted the XP outright. Since a removal only takes back what a log earned, XP can only fall short of that after an adjustment, which only `seed_demo` and tests can do, and then the database refused and the removal failed. `_take_back` now stops XP at zero and the ledger records what was actually taken.
- **"XP only goes up" against "removing a log takes back what it earned".** Both are in the UI doc. A +1 then Undo must not farm a level, so XP is never spent, and a removal takes it back. Falling below a buddy's level takes the buddy off until the level returns. Crossing it again only asks again if the sheet was never answered.
- **The sanity cap is per log, not per day: 24 hours, so 480 points at most.** The UI doc says there is no daily cap, and the brief wants a bulk +N capped. Logging 1,100 episodes in one tap pays for a day of watching, and separate logs are unaffected. Chud of the Week counts the capped hours, since it reads the ledger. Rewatches are already limited to one a title a day by tracking.
- **Idempotency.** Tracking already refuses to log the same thing twice, so a replay fires no event. As the second guard, each award has a key from the event, unique per member. A removal starts a new generation of keys, because the diary can then rightly hold the same watch again.
- **Taking back** walks awards newest first and takes each one's share, and the last of an award takes whatever is left, so the sums come to exactly nothing. It is per title, not per episode, because rows fold together: removing an old episode from the middle takes the newest award's share, which can differ by a point or two.
- **Bounties have no prototype screens**, so they follow the UI doc in the prototype's style. Only members sharing their library can have one, since "already finished" would otherwise tell you about a private library. An import never collects: "imports earn nothing". Finishing by hand after a part import does. Settling works from the entry's state on every recompute, so a season finishing airing under someone collects too, and dropping a finished title later keeps it. Undoing the finish takes the bounty and any bonus back and reopens it. A rating before finishing counts toward the bonus, a tiny bonus that rounds to 0 is nothing, and a merge that leaves two open bounties refunds the one that goes.
- **Chud of the Week** counts by the date watched, and a removal counts against that same week. Once a week is decided it stays decided. Private members can win, and their profile still shows nothing to others, crown included.
- **Other members see** level, bar, buddy and crown. Points, stickers, activity and bounties are the member's own.
- **Row locks.** Everything is one transaction in one order: tracking's advisory lock, then bounty rows, then accounts, several taken in one statement in pk order. Tokens come from the page, not per press, so a double tap is one purchase and the answer brings fresh ones.
- **The earned toast sits above sheets**, in a popover, because a +1 on TV or anime opens the rate sheet at once and a modal covers ordinary toasts. Found in the browser: with it hidden, the main logging flow never showed the amount. It sits beside M2's "Episode N logged" and Undo, which stays as it was.
- Test changes after the acceptance commit, none loosening what is checked. Three expected numbers were my arithmetic: `xp_percent(4460)` is 96, not 99 (860 of 900 into the level, as the prototype works it out and an independent review flagged), and 19,000 XP is 2,000 from level 21, not 900, by Shahan's `50 * L * (L - 1)`. The activity test bought more than it had points for. The seed tests needed `--force`. An apostrophe is escaped in HTML. The stray `make_season=None` is gone. The debt tests and `test_the_database_refuses_a_negative_balance` are replaced by the new rule, on Shahan's decision. The level-up test now expects "Not now" when there is no buddy to keep.

**Checked:** 52 guards weakened once each (`~/.cache/mediatracker/scripts/mutate_chud.py`, not committed). 49 of the first 51 went red first time. Of the other two, the import one was a real gap and has a test now, and the "bonus once" condition was redundant with the query, so it is gone and weakening the query goes red. The popover guard reads the script, because there is no JS test setup: it catches the call being removed, not being skipped, so it was also driven in a real browser. There, at 390x844 and 360x740, a +1 shows its toast above the rate sheet, a crossing raises the level-up sheet, buying and gifting on posts and comments update in place, and the negative store and bounty sheet say why. At 1440x900 Profile and store hold the column. Screenshots are in `.shots/` (not committed).

**For the PR description, where the docs and prototype differ:**
- The plan has a `stickers` table. The catalogues are in code, as the CHUD step's brief says: nothing edits them at runtime.
- The plan says balances are calculated from the ledger. There is also a stored total, to lock and read, checked against the ledger by `verify_chud`.
- The UI doc says "there's no daily cap". There isn't, but one log is capped at 24 hours, as the brief asks.
- The UI doc says "XP only goes up". A removal takes it back.
- Negative balances are Shahan's own decision and not in his docs yet.
- The prototype's level-up says "Keep my current buddy" and always has a buddy on. With none yet it says "Not now".
- The prototype shows only the CHUD toast on a +1. Here it sits beside M2's toast with its Undo.
- The prototype's Profile has no Bounties section or crown, which come from the UI doc.

### 2026-11-02: Add the CHUD acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `chud/tests/`: the level and earn sums checked against numbers from the prototype's own expressions, awards (what earns, what never does, sent twice, taking back, the cap, debt, level-ups), buying and gifting, real threads and real HTTP requests for double submits and overspends, bounties, Chud of the Week, the ledger check and the admin view, and the screens. None of the code exists yet, so they fail at this commit on purpose.

**Why:** The money rules are the sort that look right until two requests land together, so they are written down first and held to. The tests also pin the fork in the docs: `Docs/UIDesignDoc.md` on origin says "XP only goes up" and also "removing a logged episode takes back what it earned". A +1 then Undo must not farm a level, so these tests read "only goes up" as "XP is never spent", and a removal takes XP back too.

### 2026-11-02: Make the Home fallback test able to fail, and tighten two others
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Tests only, in `catalogue/tests/test_mal.py`, no code. The Home fallback test used to assert `"Popular anime" in html`, which is the carousel's heading and is drawn whether or not anything is in it. It now reads the Popular anime and Popular manga sections and checks the local titles are in them as links to their own pages. Two new tests check that the cache wins over local titles once there is one, and that each carousel falls back on its own (anime cached, manga ranking failed). The search dedupe test asserted `count("Frieren") >= 1` and a label constant, neither of which a broken dedupe would change. It now checks that MAL and AniList both found 52991 and that exactly one row stands for it, the MAL hit. The failed-refresh test also checks the rows stay listed and in place, and a new test checks an empty ranking does not wipe the set.

**Why:** A review found the fallback test could not fail. Reading the rest of the file for the same weakness turned up the dedupe test, and the failed-refresh test only counted rows, which a refresh that unlisted them would also satisfy. Weakened once each and seen red: dropping the fallback, ignoring the cache, one fallback shared by both kinds, the empty-ranking guard, a failed refresh unlisting rows, AniList outranking MAL, no dedupe at all, and the old API's name planted in a file for the scan test.

### 2026-11-02: Allow MAL's API picture hosts, and keep popular tiles' addresses stable
**Author:** Kyle Deboo (with Claude Code)

**What changed:** (1) `POSTER_HOSTS` gains `api-cdn.myanimelist.net` and `myanimelist.cdn-dena.com` next to `cdn.myanimelist.net`. (2) The daily popular refresh now upserts by `(media_type, external_id)` and no longer deletes and recreates, so a title that stays in the ranking keeps its pk. A title that drops out gets `listed=False` (new column, folded into the still-unlanded migration `0003`), leaves Home, and stays openable for a week before the same job deletes it. A title that returns is listed again. The old test that said a refresh replaces the set now says a dropped title is unlisted and Home shows only listed ones: that rule changed on purpose.

**Why:** (1) The MAL docs show picture URLs only on `myanimelist.cdn-dena.com`, the old host. The live API is understood to answer with `api-cdn.myanimelist.net`, which the docs never show. That is from memory and not verified, because there is no client id to call it with. Either way, a picture from a host not on the list would have been refused by `poster_url_allowed`, and every MAL API poster would have stayed a placeholder, so all three are allowed and a lookalike host or plain http is still refused. (2) Delete-and-recreate gave every tile a new pk each night, so a Home page left open overnight posted to a pk that no longer existed and got a 404. Tests refresh between rendering Home and posting the page's own tile addresses (all still 302), drop a title and open it from the stale page, and check the week limit and the return. Each guard weakened once went red: both hosts, the upsert, keeping dropped rows, hiding them from Home, the purge and relisting. Also retook `.shots/about-phone.png`, which predated the fix for the doubled divider between the two About sections.

### 2026-11-02: Make Home's popular tiles a POST form, not a link
**Author:** Kyle Deboo (with Claude Code)

**What changed:** A popular anime or manga tile on Home is now `<form method="post" action=".../popular/<pk>/open/">` with the CSRF token and a `<button class="tile">`, instead of an `<a>` to the same address. The form is `display: contents` and the button is reset (`button.tile` in `app.css`), so the tile looks and sits exactly as before. Tiles for titles that already exist on the server are still links. New test `test_a_popular_tile_is_a_post_form_with_a_csrf_token_not_a_link` reads Home's markup, finds no `href` to the open address, finds the form with its token, then posts with CSRF checks on: no token is a 403 and the token opens the title.

**Why:** A review found that the tile was a plain link to a view that only accepts POST, so every tap on a popular title returned 405. My earlier entry said the tile was a POST, and the markup did not do that. The existing tests posted straight to the view and never followed the markup, which is how it got through. Opening a popular tile creates a catalogue row, so it should be a POST with CSRF and not a GET with a side effect. Driven in a browser at 390 wide: tapping Death Note landed on its title page. Reverting the template to the link makes the new test go red.

### 2026-11-02: Swap Jikan for the official MAL API v2
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/upstream/jikan.py` is gone, replaced by `catalogue/upstream/mal.py` behind the same `Item` shape. Every request sends `X-MAL-Client-ID` from the new `MAL_CLIENT_ID` setting and nothing else, with no user OAuth. The pace is one request a second and a `Retry-After` is respected, both through the existing paced client. It uses `GET /anime` and `/manga` (search, with `q`, `limit`, `fields`, `nsfw`), `/anime/{id}` and `/manga/{id}` (details) and `/anime/ranking` and `/manga/ranking` with `ranking_type=bypopularity`. MAL gives an episode count, `0` for a count it does not know (read as unknown), a runtime in seconds, and `nsfw` of white, gray or black (black, an `rx` rating or a Hentai or Erotica genre is adult). The queue, lock, tasks and `SearchSource.provider` are renamed `mal` (`catalogue.search_mal`, `catalogue.mal_media_details`), and the compose worker lists `mal` in `--queues`. No deployed database has jobs under the old names, because the catalogue is not deployed yet.

With no `MAL_CLIENT_ID` MAL is off, the way TMDB is with no key: search records it as off and queues nothing, a MAL title that is opened goes straight to AniList for its details, the search results say "MyAnimeList is off: this server has no client id. AniList is covering anime and manga.", and the About page says so and names the setting. A MAL job already queued when the id is removed still ends cleanly through AniList. A search under three characters returns nothing without calling MAL, because MAL answers 400 to it.

Home's popular anime and manga now come from a new `popular_titles` table (migration `0003`, one `CreateModel`, safe on the v0.0.1 database). A daily job (`catalogue.refresh_popular_if_enabled`, 05:23) queues `catalogue.refresh_popular` only when `POPULAR_TITLES_JOB=1` and a client id is set, so it stays off in dev and tests. The refresh keeps a kind's old set when MAL fails, asks for no adult titles, and registers posters for the worker. Home reads only the table and never asks an upstream. A tile is a POST (`catalogue:open_popular`) that creates the title the first time and redirects, with the same adult check as a search hit. Until the job has run, those two carousels show what members here have logged most, as before. Movies and TV carousels are unchanged here, because TMDB popularity is not part of this step.

Also: the About page's credits (MyAnimeList, AniList, Fribb), `_source_note.html`, the search hint and its off notes, README, `.env.example`, and the recorded fixtures (`jikan_*.json` replaced by `mal_*.json`). The existing test that no template links to a third-party host now allows exactly those three About links by address, because they are credits a member can follow, not anything the page loads.

**Why:** Jikan's public API shut down on 2026-10-01 and Shahan's PR #4 makes MAL API v2 the main source for anime and manga. Optional and off-when-unset follows the TMDB decision, so an install without a client id still works. Anime episode titles already come from TMDB through Fribb (M3), so nothing there changed. Not verified: the recorded files were written from the official docs and MAL's published behaviour, not captured from live traffic, because no client id exists yet. The `media_type`, `status` and `nsfw` enum values, whether `genres` mixes in themes and demographics, and `nsfw=false` on ranking are the first things to check against the real API once there is one. At one request a second the MAL import backfill (m4) will take over 33 minutes for 2,000 titles, as the plan says. Guards weakened once each and seen red: the client id header, the missing-id refusal, search off, the AniList fallback for details, both gates on the popular job, the adult filters (Home and open), POST-only open, the short-query guard, keeping the old set on a failed refresh, the `nsfw` param, the pace, the zero-means-unknown rule and the 401 message. The origin docs (`DevelopmentPlan.md`) still name Jikan in three places, as history, and local `main` does not have PR #4 yet: `polish-pr` integrates it.

### 2026-11-02: Add the tests for the MAL API swap before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** The upstream tests now talk about MAL, not Jikan: recorded responses in MAL API v2's shape (`mal_*.json`, with the `{"data": [{"node": ...}]}` envelope, `nsfw`, `media_type`, `average_episode_duration` in seconds and `0` for an unknown count), a `upstream.mal()` helper, and the renamed queue and task names. New `catalogue/tests/test_mal.py` covers the client id header, MAL off without a client id (search, title pages, About page, source note), the popular titles cache with its daily job, the Home carousels reading it, and a scan that nothing outside the docs still says Jikan. They fail at this commit on purpose, because `catalogue/upstream/mal.py` does not exist yet.

**Why:** Jikan's public API shut down on 2026-10-01, and PR #4 on origin makes MAL API v2 the main source for anime and manga. The tests come first so the swap is held to the done criteria and not to whatever the code ends up doing. The recorded files were written from the MAL docs and not captured live, because there is no client id to call the real API with yet, so the field values (`media_type`, `status`, `nsfw`) are the documented ones and are marked as unverified against live traffic.

### 2026-11-02: Each press of Send gets its own key, made in the browser
**Author:** Kyle Deboo (with Claude Code)

**What changed:** For a form marked `data-once`, `app.js` now makes a key (`crypto.randomUUID`, then `getRandomValues`, then a timestamp with `Math.random` for a plain-http context) at the moment of the press, sends it as the token, and clears the form so a second tap falls to the browser's own "fill this in" check. The token the server drew into the page stays as the no-script fallback. The server still keeps the first comment for a token.

**Why:** A page drawn once has one server token, and offline there is no answer to bring a fresh one, so two different comments queued offline shared it and the second was dropped. A key per press fixes that, and a key made once per press is what a double tap or a queue replay of that press carries again, so it still posts once. Driven in a real browser: with the network off, "offline one" then "offline two" queued with different keys, a second tap on the emptied form queued nothing, and when the connection returned both arrived once. Online, two quick taps made one comment. There is no JS test setup here, so the tests read the script for the parts the server's rule depends on, and the server tests cover two keys from one page, three sends of one key, and the old shared-token loss. Weakening the key, the clearing and the fallback each goes red (75 guards in all, none surviving but the three equivalent ones and the early lookup noted before).

### 2026-11-02: A comment sent twice is one comment
**Author:** Kyle Deboo (with Claude Code)

**What changed:** A comment now has a `token` (`social.0002`, unique per member when set). The comment form carries a new one each time it is drawn, `add_comment` returns the comment a token already made instead of making another, and the answer to a send hands the form a fresh token. The same token on another post is refused. While a send is in flight the Send button is disabled (`data-once`, in `app.js`), unless the device is offline, where the token makes sending it again harmless.

**Why:** A double tap on Send, or the offline queue replaying a write, posted the comment twice. M2 solves this by making each write name what it means ("episode 5"), and a comment has no such name, so it gets one the form invents, the way a post already had. Checked the rest: a like is a wanted state (`on=1` twice is one like), a follow is get-or-create, and a post already carries a token, which now also has a test for a replay after the library moved on. A comment or post delete sent twice answers 404 the second time, because telling a deleted comment from one you may not see would leak that it exists; the page was already updated by the first answer. The tests for it went in first, in their own commit. Weakening the guards once each: the database constraint, the lookup that handles two sends at the same moment, the token being passed from the view, the fresh token and the disabled button all go red. Skipping the early lookup in the service does not, because the constraint and its fallback return the same comment.

### 2026-11-02: Add the tests for a comment sent twice before the fix
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `social/tests/test_replay.py`: a comment sent twice with one token is one comment, a replay is answered the same way and never overwrites it, a new token is a new comment, a token belongs to one member and to one post, and two sends at the same moment make one. It also checks likes, posts and follows sent twice. The comment ones fail at this commit on purpose.

**Why:** A reviewer found that a double tap on Send, or the offline queue replaying a write, posts the same comment twice. Posts already had a token and likes and follows are a wanted state, so those tests pass already and are here to keep it so.

### 2026-11-02: Fix what the independent read of M5 found
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- Hide comments answered 500: it rendered a template that does not exist. It now renders the same panel closed.
- A profile showed only twelve Watchlist titles, which M2's page did not, and ten posts with no way to the rest. The Watchlist is whole again, and the posts load the next page as you reach the end, from `/u/<username>/posts/?before=`, which answers 404 for a private member.
- Another member's Library now varies on `HX-Request` and `HX-History-Restore-Request`, as the member's own does, so Back can't bring up the bare fragment.
- The slide dots are 44px wide, not 34px.
- The profile header no longer says "N in Library, N on Watchlist" above a Library row that says the count. M2's test for that line now looks for the count on the row and for the line being gone.
- Each of these has a test, and each was weakened once to see it go red (7 more guards, 65 in all, none surviving apart from the three equivalent ones already noted).

**Why:** A reviewer read the branch against the brief and found these. Each was a real defect or a regression of something M2 did. One finding is not a change: the brief lists a "hold" slide, but the prototype has none. Its slides are poster, episodes and stats (`ui-logic.js`, where `kinds` is built), and "hold" there is a post variant: the banner reads "put X on hold" in blue and the stats slide is left out, which is what is built here. This goes in the PR description for Shahan.

### 2026-11-02: M5 social: follows, post composer, feed, likes, comments, profiles
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `social` app: `Follow`, `Post`, `PostLike` (with an optional `reaction`, for emoji reactions later) and `PostComment` (`is_spoiler`), all with real foreign keys. All writes go through `social/services.py`. Every read of a post starts from `social.selectors.visible_posts`.
- The Post/Skip sheet from M2 is now the composer: stars, a spoiler-free caption, a spoiler caption, Post and Skip. Skip is a button with its own `formaction` on the same form, so it sends the same stars to Rate. The queue in `app.js` reads `formaction`. A hidden token makes a double tap, or a queued write sent twice, one post.
- Posts: `/feed/` (people you follow and yourself, newest first, ten at a time, the next page loads when the last one scrolls into view), `/post/<pk>/`, edit sheet, delete with a confirm, like (a plain POST of the wanted state, so repeating it is safe), flat comments loaded on tap, `/u/<username>/` and `/u/<username>/library/` (the Library screen again, through `render_library`), `/people/` and a People row in the header search, and a members or only me switch on the member's own profile. `/me/` is the same page as anyone else's, with the member's own settings added.
- Cards follow the newer prototype: banner by outcome, swipeable slides with dots (poster, then episode scores for TV and anime, then stats), live data, an Edited marker, and a `data-sticker-slot` in every card and comment with `social/stickers.py::stickers_on` behind it, which the CHUD step fills in. Nothing of the economy is built.
- `tracking/runstats.py`: the run's total runtime, days, days on hold, average per day and the CHUD score, as arithmetic with no database plus a reader for one member's latest pass. The CHUD step's binge multiplier is meant to be built from the same figure. New `HoldSpell` (`tracking.0003`) records when a title went on hold and came off, because nothing did before, written by `set_status` and by `_resume`. `tracking/selectors.py` gains `visible_entries(owner, viewer)`, and `library_rows` and the watchlist take a `viewer`.
- Existing files touched: `config/settings.py`, `config/urls.py`, `core/urls.py` and `core/views.py` (the feed view moved to `social`), `core/templates/core/feed.html` and `accounts/templates/accounts/me.html` (deleted, replaced by `social/templates/social/feed.html` and `profile.html`), `accounts/views.py`, `catalogue/templates/catalogue/search_panel.html`, `catalogue/management/commands/seed_demo.py` (follows, posts, likes and comments for `--library-for`), `core/templatetags/ui.py` (a heart icon), `app.css`, `app.js`, `tracking/` (`models.py`, `services.py`, `selectors.py`, `views.py`, `receivers.py`, the prompt and library templates), `README.md`. Migrations are new tables only.
- Tests changed after the acceptance commit, none loosening what is checked: `tracking/tests/test_screens.py::test_post_is_a_marked_stub_...` asserted M2's disabled Post button, so it now asserts the live one and Skip's `formaction` (the stub was the thing M5 replaces). In the new tests: the privacy test no longer looks for a private member's title on Home, whose carousels list the shared catalogue, not who logged what; one profile test searched for the word "older", which the page's own CSS contains; the spoiler tests used `Episode.objects.create` for an episode a comment had already created; one stray import was removed; `ruff format` reflowed them. Tests were added for what the mutation pass found.
- 58 guards were weakened once each (`~/.cache/mediatracker/scripts/mutate_m5.py`, not committed). 47 of the first 56 went red first time. Nine did not. Four were real gaps and now have tests that go red: a private post on a shared library entry, the reveal endpoint answering for a plain comment, the refusal text for a season score that would clear episode scores, and the rating and the post sharing one transaction (a refused post left the rating changed). Two were my mutations not doing anything (one text that no longer matched, one rename of a constraint), redone against the migration and red. Three are equivalent code and left alone: the author never being blurred (their own diary covers every episode they scored), the token check before the insert (the unique constraint catches the same case), and posting a score only when it changed (rating the standing score is a no-op anyway).
- Checked in a browser at 390x844 and 1440x900: the feed, a TV post's episode slide with episodes blurred, the comments and spoiler taps, a like through the queue, the composer from logging a movie through Post to the stored row, a profile, the directory and another member's Library. Screenshots are in `.shots/` (not committed).

**Why, including every rule I had to interpret:**
- **Visibility.** The plan says `members` or `private`. Posts carry their own, from the member's default, and a post is also hidden from others when the author's library entry for that title is private, because a card shows live library data. A private member's profile says so and shows nothing else. The setting flips the member's whole library and every post in one go, since there is no per-entry screen to say otherwise. Deactivated members drop out of feeds, the directory and profiles. Adult titles follow the viewer's setting, not the author's.
- **Spoilers.** A page never contains spoiler captions, spoiler comments or the title or score of an episode the viewer is behind on. The first two load from their own endpoints on a tap. Blurred episodes are a placeholder with no title and no score, so there is nothing to read through the blur. The viewer's own post, and episodes they have logged themselves, show. An episode comment the author wrote is in the spoiler panel, because it is a comment on a specific episode and the viewer asked for spoilers.
- **What may be posted.** Only the state the title is in: finished or rewatched needs Completed, on hold needs On hold, dropped needs Dropped. The plan doesn't say; this keeps a post from saying something the library doesn't. A rewatch post is a finished post with `is_rewatch` and needs a rewatch.
- **Edited.** The plan says an edited marker shows when score, dates or captions change, but not for likes or comments, and that posts show live data. So a post stores the score and dates it was made with and compares them with the library when drawn, as well as `edited_at` for captions. A saved edit that changes nothing is not an edit.
- **A season score changed in the composer** that would clear episode scores is refused with a message that says where to do it, rather than clearing them silently. The rating and the post are one transaction.
- **On hold days.** The plan and the UI doc exclude them from stats, and nothing recorded them. `HoldSpell` is member-said data like `user_status`, so `rebuild_entries` does not touch it. The day a title comes off hold was not a day on hold, so a spell from the 25th to the 29th holds four days.
- **Which run the stats describe.** The latest pass, so a rewatch is its own run. Stats need a runtime from the source: the tracker's own 45 and 120 minute guesses are fine for progress and not for a figure someone reads. Manga is 5 minutes a chapter, as the UI doc says. The CHUD score is the day's pace over six hours, capped at 100.
- **Imports earn and post nothing,** and nothing here awards points.
- The 360x740 check from the brief was not run beyond the layout reading as one column at any width; the composer and cards use the same widths as M2 and M3 screens.

**For the PR description, where the prototype and the plan differ:**
- The prototype's slides are poster, episodes, stats, as the UI doc has them; the plan's "stats slide" appears for dropped and finished posts only. The prototype's stats slide shows a stat list and a CHUD bar. Same here, plus the on hold note.
- The prototype blurs episodes with a fake title and "0.0". Here the same words are shown, but they are placeholders: no real title or score is sent.
- The prototype puts the comment box in the card with a "Contains spoilers" checkbox. Same, loaded on tap, plus Hide comments, delete for your own comments, and for the post's author on theirs.
- The plan's `followers` visibility is dropped, as the plan says. There is no per-entry visibility screen: the one switch covers the whole library and all posts.
- The prototype's Profile also has CHUD level, buddy, stickers, store and activity. Those are the CHUD step's. This step leaves a marked slot in `social/profile.html` and in the cards.
- The prototype's Gift button on posts and comments is the CHUD step's, at `_gift_slot.html` and `social/stickers.py`.

### 2026-11-02: Add the M5 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `social/tests/`: follows, the composer (what may be posted, when, and that nothing posts on its own), the feed (who is in it, order, paging, adult titles, query count), post cards (banner, slides and dots, captions, the edited marker, live data, the sticker slot), spoilers (no spoiler text or blurred episode data in any page before the tap), privacy (private accounts, entries and watchlists across every endpoint), likes, comments, editing and deleting, the run statistics (pure arithmetic, then read from the diary, including on hold spells), profiles and the member directory. None of the code exists yet, so they fail at this commit on purpose.

**Why:** The step's done criteria are behaviour, and two of them, spoilers never in page source and private data never leaking across members, are the kind that are easy to claim and easy to break, so they are pinned down first. Stats, hold spells and the visibility setting are in the tests because the UI doc needs them and the plan does not say where they come from: days on hold are not recorded anywhere yet, so a `HoldSpell` table is part of the work.

### 2026-11-02: Close two gaps the mutation pass found in the TMDB episode path
**Author:** Kyle Deboo (with Claude Code)

**What changed:** The test for a title with no primary id now has a TMDB key, and so does the AniList-only one. The test for a mapping to a movie only now has a season on the mapping.

**Why:** 25 guards on the new episode path were weakened once each, and 23 went red. These two survived because each test passed for a different reason than it claims: with no key nothing is ever looked up, and a mapping with no season fails on the season check before reaching the show check. Both go red now. No code changed.

### 2026-11-02: Anime episode names come from TMDB through Fribb, not Jikan
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Removed `Jikan.anime_episodes`, the `jikan_anime_episodes` job and `fetch_jikan_episodes`, so `catalogue/upstream/jikan.py` is back to exactly what M1 left. There is now one episode job, `tmdb_season_episodes`, for TV and anime alike. An anime's TMDB show, season and episode offset come from its Fribb row, found by MAL id or AniList id. Its episodes are renumbered by the offset, and anything past its own count is dropped. The drill-down reads the count from `media.total_units`, which any client fills in through `Item`, so nothing in M3 knows which client that was.

**Why:** Jikan's public API shut down on 2026-10-01, and Shahan's docs change (493ac45) makes MAL API v2 the main source. It gives only a count, so names come from TMDB. This replaces what the M3 entry below says about Jikan. Rules I had to interpret:
- **Numbered rows are the design, not a fallback.** No Fribb row, a row with no TMDB show, no TMDB key: no job, no upstream call, no loader and nothing that reads as a fault. Scores, comments and roll-ups work the same on them, and a test holds that in place.
- **A mapping with no TMDB season is no match.** Fribb's `season` is optional. Guessing season 1 could put the wrong names on these rows, and a number is never wrong.
- **TMDB answering 404 for a mapped season is no match either,** because the mapping is stale, not because anything failed. It counts as fetched, so a refresh looks again later. Any other failure still shows its real reason and Try again.
- **The offset and count come from Fribb's `episode_offset.tmdb` and the title's own total.** Frieren's first three MAL entries share one TMDB season, which the AniList spike entry recorded, so without both they would all show the same names. An airing title with no count keeps every name TMDB gives after the offset, so it may show the next cours's names until its count is known.

None of this has run against live TMDB, because no key is available here. The anime season fixture and the offset behaviour follow TMDB's API reference and Fribb's real file. They still need a first live run, including the offset on a real multi-part title.

### 2026-11-02: Tests for anime episode names coming from TMDB through Fribb
**Author:** Kyle Deboo (with Claude Code)

**What changed:** `catalogue/tests/test_episodes.py` no longer expects Jikan's episode list. It now expects anime names to come from TMDB through the Fribb mapping, later parts to land on their own numbers through the mapping's episode offset, and anime with no match, no key, or a mapping that names no season to show numbered rows with no job, no upstream call and nothing that reads as a fault. Added a fixture for the anime's TMDB season, written by hand from TMDB's API reference because no key is available here, and deleted the two Jikan episode fixtures. These tests fail at this commit until the next one.

**Why:** Shahan's docs change (493ac45): Jikan's public API shut down on 2026-10-01, MAL API v2 replaces it and gives only an episode count, and titles come from TMDB through Fribb. Anime with no TMDB match showing numbered episodes is the designed behaviour, so the tests hold it to that rather than treating it as a fallback.

### 2026-11-02: Fix what an independent read of M3 found
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- A season fully logged offered "Log episode 11" of 10, a button that did nothing and then stayed disabled. It only shows now when that episode can exist. On a season of unknown length, pressing it adds the new row and moves the button on, where before it stayed disabled on the same number.
- Refreshing the list marked every row's summary as an out-of-band fragment too, so they were nested. M2's Currently list hit the same bug. The include now turns it off, and a test holds that in place.
- Removing the episode or deleting the row that holds the season score no longer loses the rating. It moves to the row before, or to a row of its own if there is none. Rate puts the score on the latest row, so it was one tap on "Remove from log" away from silently disappearing. A score a later re-rating already replaced stays gone.
- Clearing the stars on a season with only episode scores now asks "Replace episode scores?". It used to change nothing and say "Rating cleared".
- Re-rating no longer replaces the list. It updates the summaries of the rows the page has loaded, and clears the stars in open rows when it replaced them. So a half-written comment in an open row survives, and so does scroll position on a long season. The one case that still replaces the list is logging past the end of a season of unknown length.
- A double tap on the last episode lost its sheet, because the second answer changed nothing and only the last answer could open one. Now the last answer that has a sheet opens it.
- One member's stub row, made by scoring a number far past anything known, could lengthen that season's list for everyone. Rows only count for everyone if a source gave them a title. Your own scores still add rows to your own list.

**Why:** A second reader went through the diff looking for failures, and I checked each against the code before fixing it. Three of my acceptance tests had the wrong premise and are changed. `test_undoing_the_season_scored_row_takes_the_score_with_it` said the opposite of the fix above, because I had written down what the code did rather than what a member would want. `test_replacing_clears_overrides_and_refreshes_the_list` asserted the list swap that lost comments. `test_an_unrated_season_with_overrides_is_not_cleared_by_skipping` now sends what Skip really sends, the standing score, instead of None. Left alone: logging past the end of an unknown-length season still replaces the list, so a draft in an open row is lost on that one rare path, because appending a row would need a second kind of fragment in `app.js`.

Checked in a browser after the fixes: a double tap on the last episode opens the sheet once, a draft comment and its open row survive Replace with the row's stars cleared, and on a season of unknown length Log episode 1 then 2 adds a row each time with the button moving on. 16 more guards were weakened once each and went red, 98 in all across this branch. One of them, the cap on the row count, showed why the cap matters: with it removed a request asking for 999,999,999 rows tried to build them all, and I had to stop that test run. The test now tries a small number first, so the same mutant fails in a moment.

### 2026-11-02: Close the gaps the M3 mutation pass found
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added tests for an override taking the place of its range score, clearing a score past a total that shrank, the three database constraints on `episode_logs`, another member's override and comment staying out of my rows and my note, and a retry clearing its error straight away. Removed `is_season_score` from the row Rate makes when nothing is logged: a row with no range already counts as the season's score, so setting it there did nothing.

**Why:** 82 guards were weakened once each. 76 went red first time and six survived. The override test used numbers that floor to the same answer either way (6.5 and 6.8), which is exactly the kind of test a floor makes easy to write. The other four test gaps were real, and the sixth survivor was code that did nothing. Each of the five test gaps now has a test that goes red with its guard weakened, and I re-ran those five to check. Nothing in the behaviour changed.

### 2026-11-02: M3: shows, seasons, episode drill-down and roll-ups
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `tracking/rollups.py`, with no database in it, so `recompute_entry` and the screens work a season out the same way. `episode_logs` (user, episode, score, comment) holds overrides and comments, and a row only exists where there is something to say. `recompute_entry` now derives a season's score from diary ranges and overrides. `list_entries.score` on a season is the rolled up number, and `rebuild_entries` includes entries that only have episode logs. Show scores are worked out per member when asked for, with specials left out, and a season still in progress counts.
- `diary_entries.is_season_score` says a score is the default for the whole season rather than for the episodes in its row. Rate sets it, and `add_diary_row(season_score=True)` is there for M4.
- Episodes: `Tmdb.season` and `Jikan.anime_episodes`, two jobs on the existing per-source queues, and `media.episodes_fetched_at`, `episodes_requested_at` and `episodes_error`. The first drill-down queues the job. Imports, logging and the title page never do. Numbered rows work with no TMDB key, for AniList-only titles, when a source is out and while the worker is busy. An airing season refreshes after a day, a finished one at 150 days to stay inside TMDB's six months. The M6 job still has to cover seasons nobody opens.
- Screens: the older prototype's drill-down in the newer one's look (`/title/<pk>/episodes/`: expandable rows, half stars that save themselves, a comment, log and remove per episode, watched ranges, 100 rows a page, a skeleton for the first fetch, a real error with Try again), the season score note, "Replace episode scores?", View episodes on the title page, stars on the season rows and the show score on show, season and Library pages. +1 on TV and anime now opens the prototype's per-episode rate sheet, with Undo on it. Quick +1s ask about the last episode only.
- `catalogue/merge.py` is unchanged, but tracking replaces its `Episode` rule: the old one deleted a clashing episode, and the logs on it would have gone too. Comments from both sides are kept and the survivor's score stands.
- Existing files touched: `catalogue/models.py`, `services.py`, `tasks.py`, `upstream/items.py`, `tmdb.py`, `jikan.py`, `seed_demo.py`, `_season_rows.html`, `_title_body.html`, `core/templatetags/ui.py` (a comment icon), `app.css`, `app.js`, and in tracking `services.py`, `selectors.py`, `views.py`, `urls.py`, `receivers.py`, `models.py`, the title, show and prompt templates. `_merged`, `_first_gap` and friends moved from `services.py` to `rollups.py`. Both migrations are additive.
- Tests changed after the acceptance commit: `test_completing_a_season...` now presses Skip on the episode sheet before expecting the prompt, and `test_a_step_that_does_not_complete...` checks for no prompt instead of no sheet, because the M2 entry deferred the +1 sheet to here. `test_merge_with_both_logged...` now expects 8 where it expected 9, because M2 said a season score was the latest scored row until M3 replaced it, and (3 x 6 + 25 x 9) / 28 floors to 8. In the new tests: `rate(7)` in `test_logging_and_imports...` needed `replace=True`, since it rates over a bulk score, and I fixed my own arithmetic in one summary case (expected 6, is 7). Nothing checked was loosened.

**Why, including every rule I had to interpret:**
- **Which episodes count towards the average.** The plan says "effective episode scores" and doesn't say whether unwatched episodes have one. The older prototype averages over the season's whole length, watched or not, so I followed it, and that way one more +1 doesn't move a score. The length is `total_units` if known, or the highest episode the diary or an override reaches if that is higher, because a total can be wrong or missing. It does not use fetched episode rows, so a fetch can never change a score.
- **What a score on a diary range means.** The plan has a score on a range, and season scores with overrides, and doesn't say how they meet. The newer prototype's bulk sheet says "Give them all the same score" and stores it per episode. So a score logged with a range belongs to that range: 1 to 3 at four stars and 4 to 6 at one star is 2.5, not "the latest wins". It stays on the diary row instead of being copied into `episode_logs`, which keeps "only overrides stored" true and a huge range cheap. Rate says it is for the season, which is the flag, and it speaks over any range score before it. A range logged after it counts on top. Override beats range beats season score.
- **Re-rating.** The confirmation fires whenever an episode has a score of its own, from an override or a range, and the new score differs from the one standing. Clearing the rating asks too, as in the prototype. Comments survive it. The row's old score stays in the diary, since the season score now outranks it. Sending the standing score changes nothing, because Skip on a sheet sends the stars as they are. Changing a score through the edit sheet is a correction to that row and doesn't clear overrides.
- **Rating an episode does not log it,** as in the prototype. Logging earns points and a score doesn't. An entry with only episode logs has no status, so it isn't in Currently or the Library, but the title page shows its score.
- **A score alone no longer means in progress.** M2's known wart, a series rated with nothing logged showing in Currently at `0 / 10`, became reachable once episodes could be rated, so a series with no units logged now has no status.
- **Rows on the same day only fold together if their scores agree.** A row has one score, so a scored range keeps its own row rather than score the +1 next to it. An unscored +1 still joins a scored row, which M2's test requires, and takes its score.
- **Specials** are season 0 only. An anime OVA Fribb gives no season counts towards its show, because nothing marks it as a special.
- The TMDB and Jikan episode responses are written from each API's published schema and have not been compared with a live response. Jikan timed out from here again and no TMDB key is available.

**For the PR description, where the prototype and the plan differ:**
- The older prototype's episode row expands to ten numbered cells. Here it is the newer prototype's half stars plus a comment, which the older one doesn't have on a row and the plan requires.
- The older prototype heads the screen "Episodes" with nothing else. Here the heading is the season's name, with its score and watched ranges, so the screen says which season it is. Rows gain the episode's name as a second line.
- The newer prototype only offers Rate on manga in Currently, and works a season score out of episode ratings. The plan has a season score, so Rate stays on every row.
- The older prototype shows every episode's score as inherited and never logged, which the plan's rule allows. Log and remove on a row are additions, so watched ranges can be corrected without leaving the screen.
- The prototype's +1 sheet has Save and Skip. Undo is added, because the sheet covers the toast that offered it in M2.

### 2026-11-02: Add the M3 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `tracking/tests/test_rollups.py` (the plan's roll-up case word for word, averages, scores on ranges, re-rating, what an episode log can hold, show scores, specials, rebuild from the diary across TV and anime scenarios, merging), `tracking/tests/test_episode_screens.py` (the drill-down, the season score note, the re-rate confirmation, what +1 asks, show pages, the Library roll-up, linking by hand in the admin) and `catalogue/tests/test_episodes.py` (fetched on first drill-down by a worker, never by an import or a web request, numbered rows with no key or no answer, retries). None of the code exists yet, so they fail at this commit on purpose.

**Why:** M3's done criteria are behaviour, so they are pinned down first and the implementation has to meet them. The TMDB and Jikan episode files are written by hand from each API's published schema: no TMDB key is available here, and `api.jikan.moe` timed out again on 2026-11-02. They are shaped correctly but have not been compared with a live response.

### 2026-11-02: Tighten M2 after an independent read of the write path
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- The write queue is per member and does nothing signed out. Before, a write still queued when a session ended made the login page reload forever, and on a shared phone it could have gone out as the next member to sign in.
- A sent write is removed from the queue by its own id, and two tabs take turns through a lock. Before, two tabs could send one write twice and drop the one after it.
- Planned gives way to diary rows in `derive`, so a merge or an import can't leave a title planned with progress, which dropped it out of both Currently and the Library. On hold and dropped still stand.
- Log several writes only what is new around a gap, and announces only that, so hours aren't counted twice. Sending the same range again is now a no-op instead of an error, since a navigation mid-send sends it again.
- Undo takes exactly the unit it named, wherever it sits in a row, because filling a gap merges a unit into the middle of one. Undo and the Watchlist button no longer say they did something when they didn't.

**Why:** A second reader went through `tracking/services.py`, the queue and the views looking for failures, and these were what it found. Each got a test and was weakened once to see it go red, except the queue's own logic (the per-member key, the lock, removal by id), which has no automated test because this repo has no JS test setup. I checked the signed-out case and the second member in a browser. The two-tab lock is read through, not exercised. Left as they are: undoing a movie twice would remove two watches, but no screen offers that undo; rating a series with nothing logged puts it in Currently at `0 / 10`, but the title page only offers Rate once something is logged.

### 2026-11-02: M2 tracking: diary, recompute_entry, Currently, Library, Home, quick log
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `tracking` app. `diary_entries` (`watched_on` nullable, `episode_from`, `episode_to`, `volume_to`, `score` with the 1 to 10 CHECK, `source`, `import_fingerprint` unique per member) is the source of truth. `list_entries` is a projection: `status`, `progress`, `next_unit`, `progress_volumes`, `score`, `rewatch_count`, the dates and `activity_on` are written only by `recompute_entry` in `tracking/services.py`, in the same transaction as the diary change. What a member says themselves (`user_status`, `notes`, tags, favourite, visibility) stays on the row. `manage.py rebuild_entries` rebuilds everything from the diary, and `--check` reports drift without writing.
- `entry_logged` and `entry_unlogged` in `tracking/signals.py`, fired inside the transaction, so the CHUD step can award and claw back points by listening.
- Screens from the newer prototype: Currently (progress bar, +1, Log several, Rate, Put on hold, Drop), Library (type and status filters, sort, month headings, seasons under a show, 50 rows a page), Home (Continue, Recently added, and Popular per type, ranked by how many members logged it), the quick log sheet, the rate sheet, the title and show page buttons, and the Watchlist on the profile.
- Every write goes through one queue in `app.js`, kept in `localStorage`. It shows the change straight away, sends writes in order, retries quietly, waits for the connection if it has to, and on a refusal puts the page back to what the server holds and shows the real error with Try again. M0 said this queue would arrive with the first write feature.
- Existing files touched: `catalogue/services.py` announces a change of episode count or airing status through a new `catalogue/signals.py`. `catalogue/merge.py` gains `after_merge`, and tracking registers its rules. `catalogue/models.py` gains `is_whole`, `is_still_going`, `unit_word` and `minutes_per_unit`. The title and show templates, `core/views.py`, `core/urls.py`, `config/settings.py`, `config/urls.py`, `accounts/views.py`, `accounts/templates/accounts/me.html`, `core/templates/core/shell.html`, `core/templates/core/components/sheet.html` (a block so a sheet can replace its Close button), `core/templates/core/home.html`, `core/templatetags/ui.py`, `app.css`, `app.js`, `README.md`, and `seed_demo` (`--library-for`, plus logs for the fake members). `core/templates/core/currently.html`, `library.html` and `sheets/quick_log.html` moved into `tracking/templates/tracking/`.
- Test changes after the acceptance commit, none loosening what is checked: M1's `test_title_page_shows_what_the_prototype_shows` now expects the prototype's "Log movie" and "Add to Watchlist" in place of M1's stand-in labels. One screen test expected `id="title-actions"` and now expects `id="title-actions-<pk>"`, because a quick log from another title's page must not overwrite that page's buttons. One test passed an argument `Item` does not have. Tests were added for what the browser and the mutation pass turned up.
- 56 guards were weakened once each and all went red, including the advisory lock, the database constraints, merge by day, the completion rules, the one write path scan, adult filtering, CSRF, login and other members' rows. Four survived at first (the top of the score scale, a finished title with no total, a zero-unit event, specials as a next season), and each got its own test.
- Checked for real: a database migrated by the v0.0.1 code, then `migrate` from this branch, applied cleanly and `migrate --check` was happy. In a browser at 390x844, 360x740 and 1440x900: double +1, undo, finishing a title, hold and undo, bulk, offline queue and replay, a refused write, editing a log with a bad date, keyboard on the stars, Back after a filter. The queue itself has no automated test, because this repo has no JS test setup. Two bugs found only in the browser: out-of-band fragments nested inside the Currently list were thrown away, and a refused write reloaded the page forever. Both are fixed.

**Why:**
- **Progress counts what the diary covers,** not the highest episode reached, so deleting a row in the middle leaves an honest gap, +1 fills it, and a season with a gap is not complete. `next_unit` is stored because Currently needs it for every row.
- **A +1 names its episode.** That makes a double tap, and a queued write sent twice, count once. Two different +1s at the same moment both count, because an advisory lock on (user, media) queues them, which works even before the entry exists. Real threads test both.
- **Rewatches are worked out, not flagged.** The design doc's `is_rewatch` is left out: replaying the diary in date order counts full passes, so a rewatch count can't disagree with the rows it came from.
- **An entry with no rows and nothing the member set is deleted,** so a mistaken log leaves no trace, and rebuilding is exact.
- **A season score in M2 is the latest scored row.** M3 replaces this with roll-ups from `episode_logs`. Clearing a rating clears every row, or an older score would come back.
- **The date on a log is the date on the phone,** because the server runs on UTC and a Perth evening is the next day there. Up to 30 days back is accepted, for a queued write, and anything else means today.
- **A blank airing status does not hold a season open.** Only a source saying it is releasing or upcoming does, or a title whose details fetch failed could never complete. A finished title with no episode count does stay open, since nothing says that was all of it.
- **`entry_unlogged` exists** because +1 then Undo would otherwise farm points. The units logged minus the units unlogged always equals what the diary holds, and a test holds that in place. The listener runs inside the transaction, so if the CHUD ledger fails the log fails with it. That is deliberate.
- **Writes bypass htmx.** Its request queue drops anything queued on an element that has since been swapped, which is exactly what rapid +1s do, and offline replay needs its own queue anyway. Reads and sheets stay on htmx.
- **Not done on purpose:** no service worker (PWA polish is on the post-v1 backlog), so a page not already open won't load offline, and the banner says so. Notes, tags and favourite exist in the model and the service but have no screen, because the prototype has none. Swipe row actions are left out because Currently already has its buttons on the row. The Post button is a marked stub in `tracking/templates/tracking/sheets/prompt.html`, for M5.

**For the PR description, where the prototype and the plan differ:**
- The prototype raises Post/Skip on hold and drop as well as on completing. The plan only names completing. The prototype's flow is followed, since it is only a prompt and nothing posts on its own.
- The prototype opens a per-episode rate sheet after each +1 on TV and anime, and only offers Rate on manga. Per-episode scores are M3 in the plan, so here every row has Rate at season level and +1 opens nothing.
- The prototype's Home has only Popular per type. The M2 brief adds Continue and Recently added, which appear once they have something in them.
- The prototype has no way to correct a log. A "Your log" list with an edit sheet is added to the title page, because replacing another tracker needs one, and the done criteria test editing and deleting.
- The prototype's Library sets the status at 11px and Currently's secondary text at 13px. Here they are 12px and 14px, the phone minimums, and the date column is 6px wider so "Completed" fits.

### 2026-11-02: Add the M2 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `tracking/tests/`: `test_recompute.py` (add, edit, delete, merge by day, completion rules, rewatches, what the member set, rebuild equals incremental, the database constraints, a scan for a second write path), `test_concurrency.py` (real threads on real connections for a double +1), `test_events.py` (the domain event the CHUD step will listen to), `test_merge_rules.py` (`merge_media` with diaries on both sides) and `test_screens.py` (Currently, Library, Home, quick log, the rate and bulk sheets, title page actions, the Post/Skip prompt, permissions). None of the code exists yet, so they fail at this commit on purpose.

**Why:** The plan calls the diary-derived library its largest technical risk, and the step's done criteria are behaviour, so they are pinned down first and the implementation has to meet them.

### 2026-11-02: Tighten M1 after reading it back and running the full stack
**Author:** Kyle Deboo (with Claude Code)

**What changed:** A client now refuses straight away when a source is cooling down for longer than it may wait, rather than sleeping in a queue slot. Jikan's anime hits are kept when its manga request fails. A title whose details job was lost, say to a worker restart, stops its loader after two minutes and offers a retry, and a retry restarts that clock, on the row and on the object the page goes on to render. Dropped an unused attribute and moved inline imports to the top of `search.py`.

**Why:** Each was found reading the branch back, none by a failing test, so each has a new test. A real Compose run (`app`, `worker` and `db` from the built image, `migrate` as the deploy runs it) also worked end to end: the first search synced 34,221 Fribb rows from GitHub, a live search and title details ran through the worker with Jikan down, and the poster landed in the shared volume. Memory after that run was app 122 MB, worker 70 MB and db 60 MB, each under its limit, and the mapping table took 8 MB. The worker exits with a database error if it starts before `migrate` has created Procrastinate's tables, and `restart: unless-stopped` brings it back, so a first deploy recovers once `migrate` finishes. I saw the error and restarted the worker myself in that run, so the automatic recovery itself was not observed.

### 2026-11-02: AniList spike, Fribb's real shape and what the upstreams did when tried
**Author:** Kyle Deboo (with Claude Code)

**What changed:** No code. This records what the plan asked to be checked against the live services, once each, on 2026-11-02.

**Why:**
- **AniList `idMal_in` works.** Asked with real MAL ids: 50 ids returned 50 titles, all from the list. `perPage` is capped at 50, because asking for 100 still returned 50. A second page of a 150 id request returned another 50. The results come back in AniList's own order, not the order asked for, and `pageInfo` can't be trusted here (it reported `total: 5000`, `lastPage: 100` and `hasNextPage: true` for 150 ids), so the client sends one request per 50 ids and ignores it. Rate limit header at the time: `X-RateLimit-Limit: 30`. So bulk enrichment for M4 is about 1,500 titles a minute, against Jikan's 60.
- **AniList's Cloudflare bans default Python signatures.** A request with Python's default user agent got a 403 (`Error 1010: browser_signature_banned`). Every client now sends its own `User-Agent`, and a test holds that in place.
- **Fribb's file** was 7.5 MB and 39,597 entries. 8,688 have no `mal_id` and 23,556 no `anidb_id`, so AniDB can't be the only key the plan assumed. Each is unique where present, and the table keeps them as nullable unique columns. 5,376 entries have none of AniDB, MAL or AniList and are skipped, leaving 34,221 rows. `season` and `episode_offset` are each `{tvdb, tmdb}`, either key optional. This settles the plan's open question: several MAL entries do share a TMDB show (1,219 of 4,246 TV ids, up to 49 on one), told apart by `season`, though not uniquely: Frieren's first three MAL entries are all `season.tmdb: 1`.
- **Jikan was unreachable for this whole session.** `api.jikan.moe` timed out from this machine on IPv4 and IPv6 every time it was tried, while Jikan's docs site and MyAnimeList answered. So the Jikan client and its recorded files follow Jikan's published OpenAPI schema and have not been compared with a live response. The outage did test the fallback for real: Search everywhere showed Jikan's actual error and AniList's results together, and opening a title fell through to AniList.
- **TMDB could not be tried at all,** because no key was available. Its client and recorded files follow TMDB's API reference. Both need a first live run once a key is in `.env`.

### 2026-11-02: M1 catalogue: schema, worker, clients, search, posters, title pages
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- New `catalogue` app. Schema: `media` (three title columns, `show`, `season_number`, `format`, `is_adult`, `metadata_source`, an indexed `fetched_at` for the M6 refresh job), `shows`, `external_ids` (with `namespace`, `season`, and a partial unique index on primary ids with `NULLS NOT DISTINCT`), `id_mappings` shaped like Fribb, `genres`, an empty `episodes`, plus `upstream_pace`, `posters`, `sync_state` and the search result tables. Everything is additive. I ran the real path: a database migrated by the v0.0.1 code, then `migrate` from this branch, which applied cleanly and left `migrate --check` happy.
- Worker: Procrastinate, chosen in M0. The Compose `worker` is now real. There is one queue per source, and each task's `lock` makes its queue run one job at a time, all inside one process with one slot per queue. Pacing and `Retry-After` live in a Postgres row per source, so a cooldown survives a restart. A real worker ran here at 65 MB RSS against the 256 MB limit.
- Clients for TMDB, Jikan and AniList that return one plain `Item` shape, built on `httpx`. Errors carry a safe message with no URL or key, because a TMDB v3 key sits in the query string.
- Fribb sync: streamed to disk and parsed with `ijson`, replaced in one transaction, refused if the file is empty or under half the previous size, skipped on an unchanged ETag. A daily job runs it once a week, and the first search on a new install queues it. `manage.py sync_fribb` does it by hand.
- Search: typeahead reads local tables only, ignores accents and punctuation, and matches words in any order. Search everywhere queues a job per source, and the page polls for rows as they land. Results are kept in `upstream_hits`, so a `media` row only appears when a title is opened. TMDB hits that map to a MAL id are hidden and replaced by the MAL entries, with the older prototype's note. Asking again within the hour reuses the answer. Adult titles are filtered upstream, in the results, and by a 404 on opening.
- Posters: downloaded by the worker and served by the app from a shared volume, as the exact bytes upstream sent. Only three known hosts are ever fetched. Past the cap the least recently viewed go first, and past five months a file is dropped so it comes back fresh. Poster URLs are hashed into keys, so search results with no `media` row use the cache as well.
- Title and show pages from the newer prototype, with the shell's typeahead panel and Home carousels of what the server holds. `merge_media` and an admin action with a confirmation step and a **needs merge** filter. `seed_demo`, refused with `DEBUG=0`.
- Existing files touched: `config/settings.py` and `config/urls.py` (the new apps and poster settings), `core/views.py` and the shell templates (typeahead, Home, the About note), `core/static/core/css/app.css` and `js/app.js`, `docker-compose.yml`, `Dockerfile`, `requirements.txt`, `.env.example`, `.gitignore`, `.dockerignore`, `README.md`.
- Test changes after the acceptance commit, none loosening what is checked: assertions on `Sousou no Frieren` became `Beyond Journey` because a member's language defaults to English, so that is the title that shows; the anime test now answers the Jikan details call, because opening a row AniList found correctly upgrades it from Jikan; the Fribb first-run sync is stubbed in `conftest.py` and tested on its own.
- 30 guards were weakened once each and the matching test went red, including the poster host list, adult filters, overlap hiding, pacing, `Retry-After`, key leakage, the Fribb guards, merge rules, CSRF and login. One survived at first, the empty-file check, which got its own test.

**Why:**
- **Search jobs per source, not one big job,** so results appear as each source answers and an outage costs that source only.
- **AniList's `idMal_in` fetches the replacements for a hidden TMDB hit,** because one hit can stand for dozens of MAL entries. That is one request there and one per title on Jikan. At most 12 are fetched per hit.
- **Anime identity is MAL whichever client found it,** so AniList and Jikan rows for one title collapse into one, and a row found through AniList upgrades itself from Jikan when opened. AniList-only titles keep AniList as their identity.
- **Locks in one process, not a process per queue,** because four more Python processes would not fit 256 MB. The DevLog entry from M0 expected this.
- **No Caddy.** The plan allowed it for cached images, but it would have to front the app or share its port, which risks the 127.0.0.1:8990 contract, and it adds a service to run. FileResponse goes through gunicorn's sendfile and each browser only fetches a file once. I moved gunicorn to two workers with four threads each, because a page of posters is many small requests at once. If the Pi shows strain this is the first thing to revisit.
- **Polls answer 204 when nothing changed,** because swapping the rows reloaded every poster once a second and took focus away.
- **Placeholder posters** are the prototype's generated art, keyed by title. The text colour is chosen for contrast, because the prototype's fixed pairings were unreadable once titles landed on other colours, and its magenta was swapped for lilac.
- The prototype's full-bleed poster hero was kept on phones with a stronger scrim. On desktop, stretching a 342px poster across the column looks bad, so it becomes a poster beside the title.
- **Not done on purpose:** the Log and Watchlist buttons are disabled until M2 wires them. The refresh job is M6, and only its field exists here. Anime that maps to a TMDB show after the mapping appears is linked automatically, but a TMDB row whose MAL twin has never been opened can't be merged until someone opens the twin.

### 2026-11-02: Add the M1 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `catalogue/tests/` with acceptance tests for M1, a `conftest.py` that keeps the suite off the network, and recorded upstream responses in `catalogue/tests/recorded/`. The tests cover finding and opening a movie, a TV show, an anime and a manga; hiding TMDB hits that map to a MAL id and replacing them with the MAL entries; the poster cache and its cap; the refresh field; running with no TMDB key; upstream errors; adult titles; typeahead staying local; login on every page; `merge_media`; `seed_demo`; and the Compose worker. None of the code exists yet, so they fail at this commit on purpose.

**Why:** M1's done criteria are behaviour, so they are pinned down first and the implementation has to meet them. The Fribb slice and the AniList files are real responses. The TMDB files are written by hand from TMDB's API reference because no key was available, and the Jikan files from Jikan's published OpenAPI schema because `api.jikan.moe` was timing out when this was written. Those two are shaped correctly but have not been compared with a live response.
### 2026-11-02: Record on hold resume and negative balance decisions
**Author:** Shahan B

**What changed:** Updated `Docs/UIDesignDoc.md`. On hold titles now resume automatically when the next episode or chapter is logged, and removing a log can take a CHUD balance negative, which blocks spending until it's positive again. No code changed.

**Why:** Both questions were open while Kyle built the v1 branch, and the M6 review checks the build against this document. Resuming on the next log needs no extra button. Letting a balance go negative keeps the ledger accurate, and stops anyone logging a title, spending the points and then removing the log to keep them.

### 2026-11-02: Replace Jikan with the MAL API in the docs
**Author:** Shahan B

**What changed:** Updated `Docs/DevelopmentPlan.md`, `Docs/UIDesignDoc.md` and `Docs/InitialDesignDoc.md`. MAL API v2 is now the main source for anime and manga, TMDB also supplies anime episode titles, and AniList is the fallback. The plan records the `MAL_CLIENT_ID` setting for M1 and a 1 request a second starting pace. No code changed.

**Why:** Jikan's maintainer shut down the public API on 2026-10-01. The MAL API keeps the IDs that imports already use, but it needs a client ID and gives only an episode count, so episode titles come from TMDB through the Fribb mapping.

### 2026-11-02: Add CHUD activities to the design
**Author:** Shahan B

**What changed:** Added bounties, Chud of the Week and the CHUD score notes to `Docs/UIDesignDoc.md`, with an after-launch list and a list of ideas left out on purpose. Updated `Docs/DevelopmentPlan.md` with the decision, the `bounties` and `weekly_chud_winners` tables, M5 scope and the backlog.

**Why:** With no daily cap, points would pile up with little to spend them on. Bounties make recommendations a game and hold points out of circulation, and Chud of the Week gives everyone a weekly reason to come back. Both are simple, so they're in v1. Buddy upgrades follow straight after launch to solve the lack of rewards after level 20. Bets wait for real data on the economy, and daily rewards and loot boxes were rejected so the app stays fun.

### 2026-11-02: Add the CHUD system to the design
**Author:** Shahan B

**What changed:** Added section 7 to `Docs/UIDesignDoc.md`, covering points, XP, levels, buddies, stickers and the store. Updated `Docs/DevelopmentPlan.md` with the decision, the ledger and sticker tables, and M5 scope.

**Why:** The CHUD system rewards bingeing and gives friends a way to gift each other. Points use a ledger so balances can always be rebuilt and logging changes reversed. Imports earn nothing and gifts add no XP, so levels reflect real watching. Buddies are trophies only, so they stay rare. There's no daily cap because this is an invite-only group of friends.

### 2026-11-02: Update the UI design from wireframe feedback
**Author:** Shahan B

**What changed:** Added `Docs/Thoughts on wireframe.md` and updated `Docs/UIDesignDoc.md` and `Docs/DevelopmentPlan.md`. The design now asks for a score after +1, adds bulk logging with one shared score, rates movies as they're logged, moves Planned to a profile Watchlist, adds Library status filters and spoiler-marked comments, removes stats from on hold posts, and leaves on hold days out of stats. The visual direction now follows the first prototype.

**Why:** Testing the wireframe showed there was no way to rate while logging, and the Library status labels looked like filters but did nothing. The Library should also show only what defines someone's taste, so planned titles moved out. An on hold run isn't over, so stats would be misleading.

### 2026-11-02: Add the UI design document
**Author:** Shahan B

**What changed:** Added `Docs/UIDesignDoc.md` and the two diagrams in `Docs/diagrams/`. Marked `Docs/UI IDeas.md` as superseded, and kept it as the original notes. Updated `Docs/DevelopmentPlan.md` with the new navigation, Home, status and posting decisions, the `popular_titles` table, new post fields, and milestone and backlog changes.

**Why:** The UI ideas were unsettled, and several conflicted with the plan or with each other. Each decision was settled so the screens can be built from one source. Home uses a daily cache because upstream APIs must not be called on page load, and the job is off outside production so testing can't get the home IP rate limited. Whole-show posts and emoji reactions moved after v1 to limit scope, and likes store an optional reaction type so reactions need no redesign later.

### 2026-11-02: Record what the M0 branch changed in Shahan's existing files
**Author:** Kyle Deboo (with Claude Code)

**What changed:** No code. This lists every file from before this branch that was edited, so the review can find them. `config/settings.py` (apps, middleware, auth, cookies, static files, `POSTGRES_PORT`, throttle limits), `config/urls.py` (the hello page is replaced by the real routes; `/healthz` keeps the same path and body), `requirements.txt` (adds WhiteNoise), `Dockerfile` (runs `collectstatic` at build time and sets `PYTHONDONTWRITEBYTECODE`), `.env.example` (documents the new optional settings), `.gitignore` and `.dockerignore` (ignore `staticfiles/`, `.shots/` and tool caches), `manage.py` (Ruff's formatter added one blank line after the docstring, so `ruff format --check` in CI passes). `docker-compose.yml` and `release.yml` are untouched.

**Why:** CI runs `ruff format --check`, so existing files have to match the formatter. The other edits are the minimum the new apps need, and each is explained in the entry for the commit that made it.

### 2026-11-02: Stop lazy-loading the footer logo
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Removed `loading="lazy"` from the TMDB logo in the footer.

**Why:** Chrome reported a console issue for it ("lazy-loaded images should have explicit dimensions") even though the element has `width` and `height`. The logo is a 2 KB SVG that sits on every page, so deferring it saves nothing and the warning would show up in every later browser check.

### 2026-11-02: Choose Procrastinate for the worker
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Nothing in the code yet. This records the choice the plan asked for in M0. The worker will be Procrastinate (Postgres-backed, with its Django integration), added in M1 when the first job exists. The `worker` Compose service stays a placeholder until then.

**Why:** The plan said to check Procrastinate's health and compare it with Django's tasks framework. Procrastinate's health, from PyPI on 2026-11-02: version 3.10.0 released 2026-09-23, with 3.7.2, 3.7.3, 3.8.0, 3.8.1, 3.9.0 and 3.10.0 in the previous nine months, so it is actively maintained despite the maintainers' call for help. Its documentation covers what the plan needs: `procrastinate worker --queues` with `--concurrency` for one queue per source at concurrency 1, `lock` to serialise jobs for the same source, `queueing_lock` to avoid piling up duplicate jobs, and `@app.periodic(cron=...)` for the refresh jobs, deduplicated by the database across workers. Django's tasks framework is the alternative: its `django-tasks` backport (0.12.0, February 2026) is pre-1.0, and neither it nor the framework itself gives per-queue concurrency or a cron scheduler, so those would have to be written here. I did not install either; this is read from PyPI and the Procrastinate docs, not benchmarked. Revisit if Procrastinate's releases stop or the Pi's memory budget for the worker (256 MB) turns out to be too tight with it.

### 2026-11-02: Tighten the shell against the web interface guidelines, add the README
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- README: how to run with Docker Compose, create the first admin, mint and redeem codes, run the tests against a throwaway Postgres, and the production settings.
- Shell fixes from checking the screens at 390x844 and 1440x900, and against the web interface guidelines: `touch-action: manipulation` and no tap highlight, no text selection while dragging a sheet, a visually hidden `h1` on Home, `…` on busy labels and placeholders, `translate="no"` on the brand, focus moved to the first field with an error, no autofocus on form inputs (it opens the keyboard on phones), the sheet focuses its title instead of its search box, and a still spinner under reduced motion. The login page no longer shows the brand twice, the About page no longer repeats the footer attribution, the footer sits at the bottom of short pages, carousels keep their 16px lead-in when they snap, and the header search fits its full placeholder at 16px.
- Tests: the reset and deactivate tests now check the session rows are deleted before any request can notice, which the earlier version could not tell apart from Django rejecting a stale password hash. Added a 500 page test.
- Every guard was weakened once and the matching test went red: login required, throttling, ending sessions on reset and on deactivate, admin-only check, code kind, reset username binding, expiry, single use, safe `next`, CSRF, secure cookies, self-deactivation, one live reset code, and both halves of the migrate repair. Sources were restored after each.

**Why:** The shell is the foundation every later step builds on, so touch, focus and motion behaviour are fixed here once. The mutation check matters because a test that passes with the guard removed protects nothing, and it caught exactly that in the session-ending test.

### 2026-11-02: Make `migrate` safe on the deployed v0.0.1 database
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `core/management/commands/migrate.py`, which wraps Django's `migrate`, and moved `core` to the top of `INSTALLED_APPS` so its command is the one that runs. Before migrating, it looks for a database where `admin.0001_initial` is applied but `accounts.0001_initial` is not. In that case it forgets the admin app's migration history and drops the empty `django_admin_log` table, and the normal run then recreates both after `accounts`. If `django_admin_log` or `auth_user` has any rows it changes nothing and stops with an explanation. A new test builds the v0.0.1 state, shows the stock command fails on it, and checks the repair, the refusal and that nothing is touched on refusal.

**Why:** I reproduced the deploy against a database migrated by the code on `main`. With the custom user model in place, Django stops with `InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency accounts.0001_initial`. The deploy script only runs `python manage.py migrate --noinput`, so without this the first real deploy would fail on its migrate step. The v0.0.1 database has no members and an empty admin log, so rebuilding the admin tables loses nothing. The check is deliberately narrow, so it does nothing on a fresh database or one that has already been upgraded. The leftover empty `auth_user` tables from the stock auth app are harmless and left alone.

### 2026-11-02: M0 foundations: accounts, invite codes, admin panel, app shell, CI
**Author:** Kyle Deboo (with Claude Code)

**What changed:**
- Split the project into two apps. `accounts` holds the custom user model (no email; display name, avatar path, bio, default visibility `members|private`, `is_admin`, title language, show-adult flag), `invites` (signup and password-reset codes), a Postgres-backed failed-attempt throttle, the login, join, reset and sign-out screens, a `/manage/` admin panel and the `createadmin` command. `core` holds the app shell, the placeholder tabs, About, `/healthz`, `/manifest.json` and the 404, 403 and 500 pages. Django's own `/admin/` is kept and open to admins only.
- Settings: custom user model, `LoginRequiredMiddleware` so every view needs a login unless it opts out with `@login_not_required` (only login, join, reset, `/healthz` and `/manifest.json` do), secure and HttpOnly cookies when `DEBUG` is off, trust of `X-Forwarded-Proto` behind the tunnel, trusted CSRF origins derived from `ALLOWED_HOSTS`, 10 character minimum passwords, WhiteNoise for static files with fingerprinting, a `POSTGRES_PORT` override.
- Shell: base template with the prototype's tokens, self-hosted Bricolage Grotesque and Instrument Sans (SIL OFL, from the Fontsource npm packages), vendored HTMX 2.0.11, header search and initial-letter profile button, bottom tabs with the round + button, a native `<dialog>` bottom sheet (swipe down, Escape and backdrop tap close it), toasts, an offline banner and a designed empty state.
- Tooling: `pyproject.toml` (Ruff, pytest), `.pre-commit-config.yaml`, `.github/workflows/ci.yml` (Ruff, format check, `manage.py check`, migration check and pytest against a Postgres 16 service, plus a Docker build that pushes nothing). `release.yml` is untouched. The Dockerfile now runs `collectstatic` at build time, since the deploy script only runs `migrate`.
- Test fixes made while implementing, none of which loosen an assertion: the `admin_client` and `member_client` fixtures shared one client object, so the second login replaced the first; one test reused an already logged-in client for a second login; one test expected 200 or 400 where the screen correctly redirects with a message; and the sheet test now looks for the `sheet-host` element the markup actually has.

**Why:**
- A custom user model has to exist before any other migration is written, so it goes in now.
- Codes are stored as typed in the table, not hashed, so an admin can copy them again from the panel. They are single use and expire (signup 7 days, reset 24 hours), and a new reset code revokes the old one.
- Login and code attempts are counted in Postgres, not in memory, because there are two gunicorn workers and no Redis. Locked attempts get a 429.
- Redeeming a reset code ends that member's sessions explicitly as well as by changing the password hash, so the guarantee does not depend on how Django hashes sessions.
- Offline-first is not fully met by this commit. There are no writes yet to queue; the offline banner is in place and the queue arrives with the first write feature.
- Procrastinate versus Django tasks: see the separate entry for that decision.

### 2026-11-02: Add the M0 acceptance tests before the code
**Author:** Kyle Deboo (with Claude Code)

**What changed:** Added `pyproject.toml` (pytest and Ruff settings), `requirements-dev.txt`, a root `conftest.py` and acceptance tests for M0 under `accounts/tests/` and `core/tests/`. They cover username and password login with throttling, signup and password-reset codes, the admin panel, the first-admin command, the login redirect on every page, `/healthz`, the app shell, the 404 and 500 pages, the TMDB attribution, the manifest, and checks that the CI workflow and the Compose contract are intact. None of the code they test exists yet, so the whole suite fails at this commit on purpose.

**Why:** The M0 done criteria are written as behaviour, so they are pinned down as tests first and the implementation has to meet them. The next commits make them pass without changing what they assert. `pytest-env` supplies throwaway defaults for the settings that Compose normally provides, so `pytest` runs without a `.env`.

### 2026-11-01: Fix production settings being overridden
**Author:** Shahan B

**What changed:** Removed the original `SECRET_KEY`, `DEBUG = True` and `ALLOWED_HOSTS = []` lines from `config/settings.py`, which came after the new environment-based lines and overrode them. The environment-based lines now sit in their place.

**Why:** The first deploy, `v0.0.1`, ran with debug on and the committed key, and rejected the public domain with a `DisallowedHost` error. It wasn't caught earlier because `DEBUG = True` with an empty `ALLOWED_HOSTS` still accepts `localhost` and `127.0.0.1`, so the local checks and the deploy's health check all passed. The key committed to git was only ever a development key and must not be used in production.

### 2026-11-01: Build the release image with GitHub Actions
**Author:** Shahan B

**What changed:** Added `.github/workflows/release.yml`. Pushing any tag now builds a `linux/arm64` image and publishes it to GHCR as `ghcr.io/shahanb/mediatracker:<tag>`. The workflow doesn't run tests yet because none exist.

**Why:** This is the next part of M0. The deploy script pulls a tagged image from GHCR, so one has to exist before the first deploy. The image must be arm64 because the Pi is aarch64. It's built under emulation on GitHub's standard runners, which is slower but works for a private repo.

### 2026-11-01: Run the app in Docker with Gunicorn and Postgres
**Author:** Shahan B

**What changed:** Added a `Dockerfile`, `.dockerignore`, `docker-compose.yml` and `.env.example`, and added Gunicorn and psycopg to `requirements.txt`. `config/settings.py` now reads its secret key, debug flag, allowed hosts and database settings from environment variables, and uses Postgres instead of SQLite. Compose runs `app`, `worker` and `db`, publishes the app on `127.0.0.1:8990` only, and sets a `mem_limit` on each service. `worker` is a placeholder that stays idle until a task runner is chosen. Checked locally: `/` and `/healthz` respond through Gunicorn, and all 18 Django migrations applied to Postgres.

**Why:** This is the next part of M0, and it makes local runs match how the app will run on the Pi. The service names, port binding and memory limits follow the requirements in `Docs/DevelopmentPlan.md`. Kyle confirmed that the deploy script passes the image tag as `TAG` and reads the database name and user from the `db` container's environment, so neither needs extra configuration. Because settings now come from `.env`, the app has to be run through Compose instead of plain `runserver`.

### 2026-11-01: Add the Django project with a hello page and health check
**Author:** Shahan B

**What changed:** Added a Django 5.2 project in `config/` with `manage.py`, a `requirements.txt` and a `.gitignore`. `/` returns `hello`, `/healthz` returns `ok`, and `/admin/` is Django's default admin. Both new pages were checked with the local development server. The database and login are not set up yet.

**Why:** This is the first part of M0, which gets a minimal page deployed before there is real data to break. `/healthz` is included from the start because the deploy script polls it to decide whether to roll back. It has no trailing slash because the script calls that exact path.

### 2026-11-01: Add the dev log and a commit check
**Author:** Shahan B

**What changed:** Added this file, a `pre-commit` hook in `.githooks/` that rejects commits which don't add to this file, and `CLAUDE.md` with the same rule for Claude Code. The three entries below were backfilled from the git history.

**Why:** To keep a readable explanation of why each change was made, which commit messages alone don't give. A hook enforces the rule, so it doesn't rely on anyone remembering.

### 2026-11-01: Add Kyle's host details to the plan
**Author:** Kyle Deboo

**What changed:** Updated `Docs/DevelopmentPlan.md` section 5 with the deployment flow, the commands available to the `mt-deploy` and `mt-files` accounts, the host details, and the questions still open for Kyle. Merged through PR #1.

**Why:** Kyle finished setting up the server, so the plan's deployment assumptions could be replaced with the real set-up. The new section takes priority over the earlier version.

### 2026-11-01: Initial commit
**Author:** Shahan B

**What changed:** Added `Docs/InitialDesignDoc.md` and `Docs/DevelopmentPlan.md`.

**Why:** To record the design and milestones before any code is written.
