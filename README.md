# MediaTracker UI update

UI changes for MediaTracker, handed over as one patch so they can be committed as your own work.

Includes:
- Profile redesign: left-aligned header, Posts / Favourites / Stats tabs, activity "Show more", star badges, stock avatars
- Settings "Me" section: name, username, tap-to-reveal avatar picker
- Notifications page with the top-bar bell
- CHUD: level hero, buddy roster, bounty cards (poster behind bars, 14-day window, refund on expiry)

## Apply

The patch is against commit `6121243` (v1.2-era `main`). `origin/main` has moved on, so expect conflicts in
the profile, notifications, shell, settings and CHUD files.

    git checkout -b ui-update origin/main
    git apply --3way ui-update.patch
    # resolve conflicts, run the tests, then commit

`changed-files/` holds the final version of every added or modified file at its repo path, for reading
or for taking a file whole where your side has nothing to keep.
