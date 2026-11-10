"""The single write path for CHUD. Every change to a balance goes through `_record`, which writes
the ledger row and the stored total together, inside a transaction holding the account's row lock.

Lock order, so nothing can deadlock: the tracking advisory lock on (member, title), then bounty
rows, then account rows, several of which are always taken in one statement in pk order.
"""

from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from accounts.models import User
from social.models import Post
from tracking import runstats
from tracking import services as tracking
from tracking.models import DiaryEntry, ListEntry, Status

from . import notices, rules
from .models import Bounty, ChudAccount, ChudLedger, StickerGift, UserSticker, WeeklyChudWinner

Kind = ChudLedger.Kind


class ChudError(Exception):
    """A spend that can't happen. The message is safe to show a member."""


def _accounts(*user_ids):
    """Lock these members' accounts, making any that don't exist yet. {user id: account}."""
    ids = sorted(set(user_ids))

    def read():
        locked = ChudAccount.objects.select_for_update().filter(user_id__in=ids).order_by("user_id")
        return {account.user_id: account for account in locked}

    found = read()
    if len(found) < len(ids):
        ChudAccount.objects.bulk_create(
            [ChudAccount(user_id=pk) for pk in ids if pk not in found], ignore_conflicts=True
        )
        found = read()
    return found


def _record(account, kind, text, points=0, xp=0, **links):
    account.points += points
    account.xp += xp
    account.save(update_fields=["points", "xp"])
    return ChudLedger.objects.create(
        user_id=account.user_id, kind=kind, text=text, points=points, xp=xp, **links
    )


def _check_can_spend(account, price):
    """The one check every spend goes through. A balance that isn't positive spends nothing at all,
    whatever the price."""
    blocked = rules.spend_block(account.points)
    if blocked:
        raise ChudError(blocked)
    if account.points < price:
        raise ChudError(f"You need {rules.points_short(price - account.points)}.")


def _debit(account, kind, text, price, **links):
    """Points going out, which have to be there."""
    _check_can_spend(account, price)
    return _record(account, kind, text, points=-price, **links)


def _take_back(account, kind, text, amount, xp=0, **links):
    """Points the member should not have had, all of them, even past zero if they were spent. XP
    stops at zero: a removal can only ever reach below it after an adjustment took XP away."""
    return _record(account, kind, text, points=-amount, xp=-min(xp, account.xp), **links)


def _sticker(sticker_id):
    found = rules.sticker(sticker_id)
    if found is None:
        raise ChudError("That sticker isn't in the store.")
    return found


def _level_changed(account, offer=True):
    """After XP moved: raise the level-up sheet if a buddy was crossed, or take back an offer if
    it no longer holds."""
    level = rules.level_for(account.xp)
    fields = []
    if level > account.peak_level:
        crossed = rules.buddies_crossed(account.peak_level, level)
        if crossed and offer:
            account.pending_buddy = crossed[-1].id
            fields.append("pending_buddy")
            notices.level_up()
        account.peak_level = level
        fields.append("peak_level")
    elif account.pending_buddy and rules.buddy(account.pending_buddy).level > level:
        account.pending_buddy = ""
        account.peak_level = level
        fields += ["pending_buddy", "peak_level"]
    if fields:
        account.save(update_fields=fields)


# Earning: called from receivers.py, inside the transaction that changed the diary


def _watched_words(media, user, units, first):
    title = media.title_for(user)
    if media.is_whole:
        return title
    word = media.unit_word
    if units == 1 and first:
        return f"{word} {first} of {title}"
    return f"{units} {word.lower()}s of {title}"


def award(user, media, units, hours, at, event="", first=None, row=None):
    """Points and XP for a log. `event` names what happened, so the same one announced twice earns
    once. A removal starts a new generation, because the diary can then hold the same thing again.
    """
    account = _accounts(user.pk)[user.pk]
    key = ""
    if event:
        generation = ChudLedger.objects.filter(user=user, media=media, kind=Kind.UNEARN).count()
        key = f"earn:{media.pk}:{generation}:{event}"
        if ChudLedger.objects.filter(user=user, key=key).exists():
            return None
    hours = rules.capped_hours(hours)
    amount = rules.earned(hours, *runstats.pace_for(user, media))
    words = _watched_words(media, user, units, first)
    found = _record(
        account,
        Kind.EARN,
        f"Logged {words}" if media.is_whole else words,
        points=amount,
        xp=amount,
        media=media,
        diary_entry=row,
        units=units,
        minutes=round(hours * 60),
        watched_on=at,
        key=key,
    )
    _level_changed(account)
    notices.earned(amount)
    return found


def take_back(user, media, units, first=None):
    """A removal gives back what those units earned, newest award first. A log that paid for
    several gives back its share, and the last of it gives back whatever is left, so the sums come
    to nothing. Anything logged before this layer existed has no award and takes nothing."""
    awards = list(ChudLedger.objects.filter(user=user, media=media, kind=Kind.EARN).order_by("-pk"))
    if not awards:
        return
    taken = {
        row["reverses_id"]: row
        for row in ChudLedger.objects.filter(reverses__in=awards)
        .values("reverses_id")
        .annotate(units=Sum("units"), points=Sum("points"), minutes=Sum("minutes"))
    }
    account = _accounts(user.pk)[user.pk]
    left = units
    for award_row in awards:
        if not left:
            break
        gone = taken.get(award_row.pk, {"units": 0, "points": 0, "minutes": 0})
        open_units = award_row.units - gone["units"]
        if open_units <= 0:
            continue
        open_points = award_row.points + gone["points"]
        open_minutes = award_row.minutes + gone["minutes"]
        count = min(left, open_units)
        share = (
            open_points if count == open_units else rules._round(open_points * count / open_units)
        )
        minutes = (
            open_minutes if count == open_units else rules._round(open_minutes * count / open_units)
        )
        words = _watched_words(media, user, count, first if count == 1 else None)
        _take_back(
            account,
            Kind.UNEARN,
            f"Removed {words}",
            share,
            xp=share,
            media=media,
            units=count,
            minutes=-minutes,
            watched_on=award_row.watched_on,
            reverses=award_row,
        )
        left -= count
    _level_changed(account)


# Stickers


@transaction.atomic
def buy_sticker(user, sticker_id, token=""):
    sticker = _sticker(sticker_id)
    account = _accounts(user.pk)[user.pk]
    key = f"buy:{token}" if token else ""
    if key and ChudLedger.objects.filter(user=user, key=key).exists():
        return
    _debit(account, Kind.BUY, f"Bought {sticker.name}", sticker.price, sticker=sticker.id, key=key)
    owned, _ = UserSticker.objects.select_for_update().get_or_create(user=user, sticker=sticker.id)
    owned.count += 1
    owned.save(update_fields=["count"])


@transaction.atomic
def send_sticker(sender, target, sticker_id, from_collection=False, token=""):
    """`target` is a post or a comment. `from_collection` says the sheet offered one they own, so
    a stale sheet can never charge for what it said was free."""
    sticker = _sticker(sticker_id)
    recipient = target.user
    if recipient.pk == sender.pk:
        raise ChudError("You can't send a sticker to your own post or comment.")
    if not recipient.is_active:
        raise ChudError(f"{recipient.name} has left the group.")
    accounts = _accounts(sender.pk, recipient.pk)
    if token:
        sent = StickerGift.objects.filter(sender=sender, token=token).first()
        if sent:
            return sent
    gift = StickerGift(
        sender=sender,
        recipient=recipient,
        sticker=sticker.id,
        payout=sticker.payout,
        token=token,
        price_paid=0 if from_collection else sticker.price,
        **({"post": target} if isinstance(target, Post) else {"comment": target}),
    )
    words = f"Sent {sticker.name} to {recipient.name}"
    if from_collection:
        owned = (
            UserSticker.objects.select_for_update()
            .filter(user=sender, sticker=sticker.id, count__gt=0)
            .first()
        )
        if owned is None:
            raise ChudError(f"You don't have a {sticker.name} left.")
        owned.count -= 1
        owned.save(update_fields=["count"])
        gift.save()
        _record(
            accounts[sender.pk],
            Kind.GIFT_SENT,
            words,
            counterparty=recipient,
            gift=gift,
            sticker=sticker.id,
        )
    else:
        # A refusal in `_debit` rolls this back with the rest of the transaction.
        gift.save()
        _debit(
            accounts[sender.pk],
            Kind.GIFT_SENT,
            words,
            sticker.price,
            counterparty=recipient,
            gift=gift,
            sticker=sticker.id,
        )
    _record(
        accounts[recipient.pk],
        Kind.GIFT_RECEIVED,
        f"{sender.name} sent you {sticker.name}",
        points=sticker.payout,
        counterparty=sender,
        gift=gift,
        sticker=sticker.id,
    )
    stk, _ = UserSticker.objects.select_for_update().get_or_create(
        user=recipient, sticker=sticker.id, defaults={"count": 0}
    )
    stk.count += 1
    stk.save(update_fields=["count"])
    return gift


# Buddies


def set_buddy(user, buddy_id):
    buddy = rules.buddy(buddy_id)
    if buddy is None:
        raise ChudError("There is no buddy by that name.")
    xp = ChudAccount.objects.filter(user=user).values_list("xp", flat=True).first() or 0
    if rules.level_for(xp) < buddy.level:
        raise ChudError(f"{buddy.name} unlocks at level {buddy.level}.")
    user.chud_buddy = buddy.id
    user.save(update_fields=["chud_buddy", "updated_at"])


@transaction.atomic
def answer_level_up(user, equip):
    account = _accounts(user.pk)[user.pk]
    pending = account.pending_buddy
    if not pending:
        return
    account.pending_buddy = ""
    account.save(update_fields=["pending_buddy"])
    if equip:
        set_buddy(user, pending)


# Bounties


@transaction.atomic
def place_bounty(sender, recipient, media, amount, token=""):
    if token:
        placed = Bounty.objects.filter(sender=sender, token=token).first()
        if placed:
            return placed
    if amount < 1:
        raise ChudError("A bounty has to be at least 1 point.")
    if recipient.pk == sender.pk:
        raise ChudError("You can't put a bounty on yourself.")
    if not recipient.is_active or recipient.default_visibility != User.Visibility.MEMBERS:
        raise ChudError(f"You can't put a bounty on {recipient.name}.")
    if media.is_adult and not recipient.show_adult:
        raise ChudError(f"{recipient.name} doesn't see adult titles.")
    # Rolled back with everything else if this is refused. It also takes the tracking lock, which
    # has to come before the account's: see the top of this file.
    entry = tracking.set_watchlist(recipient, media, True)
    if entry is not None and entry.status == Status.COMPLETED:
        raise ChudError(f"{recipient.name} has already finished it.")
    account = _accounts(sender.pk)[sender.pk]
    if token:
        placed = Bounty.objects.filter(sender=sender, token=token).first()
        if placed:
            return placed
    if Bounty.objects.filter(
        sender=sender, recipient=recipient, media=media, status=Bounty.Status.OPEN
    ).exists():
        raise ChudError(f"You already have a bounty on this for {recipient.name}.")
    # A refusal in `_debit` rolls this back with the rest of the transaction.
    bounty = Bounty.objects.create(
        sender=sender,
        recipient=recipient,
        media=media,
        amount=amount,
        token=token,
        expires_at=timezone.now() + timedelta(days=rules.BOUNTY_WINDOW_DAYS),
    )
    _debit(
        account,
        Kind.BOUNTY_SET,
        f"Bounty on {media.title_for(sender)} for {recipient.name}",
        amount,
        counterparty=recipient,
        media=media,
        bounty=bounty,
    )
    return bounty


@transaction.atomic
def cancel_bounty(bounty, user):
    bounty = Bounty.objects.select_for_update().select_related("media").get(pk=bounty.pk)
    if bounty.sender_id != user.pk:
        raise ChudError("That isn't your bounty.")
    if bounty.status == Bounty.Status.CANCELLED:
        return bounty
    if bounty.status == Bounty.Status.COLLECTED:
        raise ChudError("It has already been collected.")
    account = _accounts(user.pk)[user.pk]
    _record(
        account,
        Kind.BOUNTY_REFUND,
        f"Cancelled bounty on {bounty.media.title_for(user)}",
        points=bounty.amount,
        counterparty_id=bounty.recipient_id,
        media=bounty.media,
        bounty=bounty,
    )
    bounty.status = Bounty.Status.CANCELLED
    bounty.settled_at = timezone.now()
    bounty.save(update_fields=["status", "settled_at"])
    return bounty


def _logged_by_hand(user, media):
    rows = DiaryEntry.objects.filter(user=user, media=media, source=DiaryEntry.Source.MANUAL)
    return rows.exists() if media.is_whole else rows.filter(episode_from__isnull=False).exists()


def settle_bounties(user, media, entry):
    """Pay what this entry now earns. Called on every recompute and works from the state, not from
    what just happened, so finishing is caught however it came about: a log, a season that finished
    airing, a status handed back to the diary. An import alone never collects."""
    if entry is None or entry.status != Status.COMPLETED:
        return
    bounties = list(
        Bounty.objects.select_for_update(of=("self",))
        .filter(
            Q(status=Bounty.Status.OPEN) | Q(status=Bounty.Status.COLLECTED, bonus_paid=False),
            recipient=user,
            media=media,
        )
        .select_related("sender")
        .order_by("pk")
    )
    if not bounties:
        return
    by_hand = _logged_by_hand(user, media)
    if not by_hand and all(b.status == Bounty.Status.OPEN for b in bounties):
        return
    accounts = _accounts(user.pk, *[b.sender_id for b in bounties])
    for bounty in bounties:
        if bounty.status == Bounty.Status.OPEN:
            if bounty.expires_at and bounty.expires_at <= timezone.now():
                # The window closed before the friend finished it: the sender's points go back.
                _record(
                    accounts[bounty.sender_id],
                    Kind.BOUNTY_REFUND,
                    f"Bounty on {media.title_for(bounty.sender)} expired",
                    points=bounty.amount,
                    counterparty=user,
                    media=media,
                    bounty=bounty,
                )
                bounty.status = Bounty.Status.CANCELLED
                bounty.settled_at = timezone.now()
                bounty.save(update_fields=["status", "settled_at"])
                continue
            if not by_hand:
                continue
            _record(
                accounts[user.pk],
                Kind.BOUNTY_COLLECT,
                f"{bounty.sender.name}'s bounty on {media.title_for(user)}",
                points=bounty.amount,
                counterparty=bounty.sender,
                media=media,
                bounty=bounty,
            )
            notices.line(f"+{bounty.amount} CHUD points from {bounty.sender.name}'s bounty")
            bounty.status = Bounty.Status.COLLECTED
            bounty.settled_at = timezone.now()
        if entry.score is not None and entry.score >= rules.BONUS_SCORE:
            bonus = rules.taste_bonus(bounty.amount)
            if bonus:
                title = media.title_for(bounty.sender)
                _record(
                    accounts[bounty.sender_id],
                    Kind.BOUNTY_BONUS,
                    f"{user.name} rated {title} 4 stars or higher",
                    points=bonus,
                    counterparty=user,
                    media=media,
                    bounty=bounty,
                )
            bounty.bonus_paid = True
        bounty.save(update_fields=["status", "settled_at", "bonus_paid"])


def reopen_bounties(user, media):
    """A log was removed and the title is no longer finished, so what finishing paid goes back and
    the bounty is open again. The setter can then cancel it for their refund."""
    status = (
        ListEntry.objects.filter(user=user, media=media).values_list("status", flat=True).first()
    )
    if status == Status.COMPLETED:
        return
    bounties = list(
        Bounty.objects.select_for_update(of=("self",))
        .filter(status=Bounty.Status.COLLECTED, recipient=user, media=media)
        .select_related("sender")
        .order_by("pk")
    )
    if not bounties:
        return
    accounts = _accounts(user.pk, *[b.sender_id for b in bounties])
    title = media.title_for(user)
    for bounty in bounties:
        if Bounty.objects.filter(
            sender=bounty.sender_id, recipient=user, media=media, status=Bounty.Status.OPEN
        ).exists():
            continue
        _take_back(
            accounts[user.pk],
            Kind.BOUNTY_RETURN,
            f"Took back {bounty.sender.name}'s bounty on {title}",
            bounty.amount,
            counterparty=bounty.sender,
            media=media,
            bounty=bounty,
        )
        bonus = rules.taste_bonus(bounty.amount) if bounty.bonus_paid else 0
        if bonus:
            _take_back(
                accounts[bounty.sender_id],
                Kind.BOUNTY_RETURN,
                f"Took back the taste bonus on {media.title_for(bounty.sender)}",
                bonus,
                counterparty=user,
                media=media,
                bounty=bounty,
            )
        bounty.status = Bounty.Status.OPEN
        bounty.bonus_paid = False
        bounty.settled_at = None
        bounty.save(update_fields=["status", "bonus_paid", "settled_at"])


# Chud of the Week


def _week_before(day):
    from datetime import timedelta

    return day - timedelta(days=day.weekday() + 7)


def decide_week(today=None):
    """Decide the last whole week, Monday to Sunday, if it hasn't been. A week nobody logged in has
    no winner, and the crown stays where it was. Run again it changes nothing."""
    from datetime import timedelta

    week = _week_before(today or timezone.localdate())
    if WeeklyChudWinner.objects.filter(week=week).exists():
        return []
    totals = (
        ChudLedger.objects.filter(
            kind__in=(Kind.EARN, Kind.UNEARN),
            watched_on__gte=week,
            watched_on__lte=week + timedelta(days=6),
            user__is_active=True,
        )
        .values("user_id")
        .annotate(total=Sum("minutes"))
        .filter(total__gt=0)
    )
    best = max((row["total"] for row in totals), default=0)
    winners = [
        WeeklyChudWinner(week=week, user_id=row["user_id"], minutes=best)
        for row in totals
        if row["total"] == best
    ]
    WeeklyChudWinner.objects.bulk_create(winners, ignore_conflicts=True)
    return winners


# The books


def verify():
    """Everywhere the ledger and the stored numbers disagree. Empty on a healthy database."""
    problems = []
    summed = {
        row["user_id"]: row
        for row in ChudLedger.objects.values("user_id").annotate(points=Sum("points"), xp=Sum("xp"))
    }
    accounts = {a.user_id: a for a in ChudAccount.objects.all()}
    names = dict(User.objects.values_list("pk", "username"))
    for pk in sorted(set(summed) | set(accounts)):
        right = summed.get(pk, {"points": 0, "xp": 0})
        account = accounts.get(pk) or ChudAccount(user_id=pk)
        for name in ("points", "xp"):
            stored = getattr(account, name)
            if stored != right[name]:
                problems.append(f"{names[pk]}: stored {name} {stored}, ledger says {right[name]}")
    counts = {}
    for row in ChudLedger.objects.filter(kind=Kind.BUY).values("user_id", "sticker"):
        counts[(row["user_id"], row["sticker"])] = (
            counts.get((row["user_id"], row["sticker"]), 0) + 1
        )
    for row in ChudLedger.objects.filter(kind=Kind.GIFT_SENT, points=0).values(
        "user_id", "sticker"
    ):
        counts[(row["user_id"], row["sticker"])] = (
            counts.get((row["user_id"], row["sticker"]), 0) - 1
        )
    for row in ChudLedger.objects.filter(kind=Kind.GIFT_RECEIVED).values(
        "user_id", "sticker"
    ):
        counts[(row["user_id"], row["sticker"])] = (
            counts.get((row["user_id"], row["sticker"]), 0) + 1
        )
    for owned in UserSticker.objects.all():
        counts.setdefault((owned.user_id, owned.sticker), 0)
    stored_counts = {(o.user_id, o.sticker): o.count for o in UserSticker.objects.all()}
    for (pk, sticker), right in sorted(counts.items()):
        stored = stored_counts.get((pk, sticker), 0)
        if stored != right:
            problems.append(f"{names[pk]}: owns {stored} {sticker}, ledger says {right}")
    return problems


@transaction.atomic
def repair():
    """Set every stored balance to what the ledger says. The ledger is the truth."""
    summed = ChudLedger.objects.values("user_id").annotate(points=Sum("points"), xp=Sum("xp"))
    known = set()
    for row in summed:
        known.add(row["user_id"])
        account = _accounts(row["user_id"])[row["user_id"]]
        account.points, account.xp = row["points"], row["xp"]
        account.save(update_fields=["points", "xp"])
    ChudAccount.objects.exclude(user_id__in=known).update(points=0, xp=0)


@transaction.atomic
def adjust(user, points=0, xp=0, text="Adjustment"):
    """Points or XP from nowhere, on the record. Only `seed_demo` and tests call this: nothing a
    member can do reaches it."""
    account = _accounts(user.pk)[user.pk]
    _record(account, Kind.ADJUST, text, points=points, xp=xp)
    _level_changed(account, offer=False)
