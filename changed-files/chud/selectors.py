"""Reading CHUD: balances, what a screen shows. A member's points, stickers, activity and bounties
are theirs alone; other members see only the level, the buddy and the crown."""

import uuid
from dataclasses import asdict

from django.db.models import Count, DurationField, ExpressionWrapper, F, Max, Q
from django.db.models.functions import Now

from accounts.models import User

from . import rules
from .models import Bounty, ChudAccount, ChudLedger, StickerGift, UserSticker, WeeklyChudWinner

RECENT = 12
ACTIVITY_SHOWN = 4


def account(user):
    """Their balances, or an empty account if nothing has happened to them yet."""
    return ChudAccount.objects.filter(user=user).first() or ChudAccount(user=user)


def level(user):
    return rules.level_for(account(user).xp)


def active_buddy(user, at_level=None):
    """Their chosen buddy, if their level still reaches it."""
    chosen = rules.buddy(user.chud_buddy)
    if chosen is None:
        return None
    reached = level(user) if at_level is None else at_level
    return chosen if chosen.level <= reached else None


def crowned():
    """Who holds the crown: the latest winners, until the next are decided."""
    week = WeeklyChudWinner.objects.aggregate(week=Max("week"))["week"]
    if week is None:
        return set()
    return set(WeeklyChudWinner.objects.filter(week=week).values_list("user_id", flat=True))


def _owned(user):
    return dict(UserSticker.objects.filter(user=user, count__gt=0).values_list("sticker", "count"))


def owned_stickers(user):
    counts = _owned(user)
    return [
        {**asdict(k), "count": counts[k.id], "aria": f"{k.name}, {counts[k.id]}"}
        for k in rules.STICKERS
        if k.id in counts
    ]


def _activity_row(row):
    if row.points > 0:
        amount, tone = f"+{row.points}", "up"
    elif row.points == 0 and row.kind == ChudLedger.Kind.GIFT_SENT:
        amount, tone = "From collection", "down"
    else:
        amount, tone = str(row.points), "down"
    return {"text": row.text, "amount": amount, "tone": tone}


def recent_activity(user, limit=RECENT):
    rows = (
        ChudLedger.objects.filter(user=user)
        .exclude(kind=ChudLedger.Kind.ADJUST)
        .exclude(kind__in=[
            ChudLedger.Kind.BOUNTY_SET,
            ChudLedger.Kind.BOUNTY_REFUND,
            ChudLedger.Kind.BOUNTY_COLLECT,
            ChudLedger.Kind.BOUNTY_BONUS,
            ChudLedger.Kind.BOUNTY_RETURN,
        ])
        .order_by("-pk")[:limit]
    )
    return [_activity_row(row) for row in rows]


def buddy_grid(user, at_level):
    active = active_buddy(user, at_level)
    grid = []
    for b in rules.BUDDIES:
        locked = b.level > at_level
        is_active = active is not None and active.id == b.id
        if locked:
            aria = f"{b.name}, unlocks at level {b.level}"
            caption = f"Level {b.level}"
        elif is_active:
            aria, caption = f"{b.name}, your CHUD buddy", b.name
        else:
            aria, caption = f"Set {b.name} as your CHUD buddy", "Set"
        grid.append(
            {**asdict(b), "locked": locked, "active": is_active, "aria": aria, "caption": caption}
        )
    return grid


def buddy_context(user, at_level):
    return {
        "buddy_now": active_buddy(user, at_level),
        "buddy_grid": buddy_grid(user, at_level),
        "first_buddy": rules.next_buddy(at_level),
    }


def profile(owner, viewer):
    """What the Profile shows of CHUD, for this viewer."""
    found = account(owner)
    at_level = rules.level_for(found.xp)
    context = {
        "level": at_level,
        "percent": rules.xp_percent(found.xp),
        "crowned": owner.pk in crowned(),
        "buddy_now": active_buddy(owner, at_level),
    }
    if owner.pk == viewer.pk:
        context |= {
            "mine": True,
            "points": found.points,
            "points_text": rules.points_text(found.points),
            "xp_line": rules.xp_line(found.xp),
            "owned": owned_stickers(owner),
            "activity": recent_activity(owner),
            **buddy_context(owner, at_level),
            **bounties(owner),
        }
    return context


def bounties(user):
    """The member's open bounties, live ones annotated with time_left. Expired ones stay in
    bounties_i_set (with an Expired tag and the Cancel to reclaim) and leave bounties_on_me."""
    open_ones = Bounty.objects.filter(status=Bounty.Status.OPEN).select_related(
        "sender", "recipient", "media", "media__show"
    )
    wrap = {"time_left": ExpressionWrapper(F("expires_at") - Now(), output_field=DurationField())}
    live = open_ones.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=Now())).annotate(**wrap)
    return {
        "bounties_on_me": list(live.filter(recipient=user).order_by("-pk")),
        "bounties_i_set": list(live.filter(sender=user).order_by("-pk"))
        + list(
            open_ones.filter(sender=user, expires_at__lte=Now()).annotate(**wrap).order_by("-pk")
        ),
    }


def bounties_here(user, media):
    return (
        Bounty.objects.filter(recipient=user, media=media, status=Bounty.Status.OPEN)
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=Now()))
        .select_related("sender")
    )


def bounty_candidates(user, media):
    """Who this member can put a bounty on. A private member's library is nobody's business, so
    they are not on the list, and neither is someone who has not asked for adult titles."""
    found = User.objects.filter(is_active=True, default_visibility=User.Visibility.MEMBERS).exclude(
        pk=user.pk
    )
    if media.is_adult:
        found = found.filter(show_adult=True)
    return found.order_by("display_name", "username")


def _short_note(points, price):
    """How far off it is. Below zero the screen says why instead: see `rules.spend_block`."""
    short = price - points
    return f". {rules.points_short(short)} needed" if short > 0 and points >= 0 else ""


def _too_poor(points, price):
    return points <= 0 or points < price


def store_rows(user):
    points = account(user).points
    counts = _owned(user)
    rows = []
    for k in rules.STICKERS:
        note = f"You own {counts[k.id]}" if k.id in counts else f"Friend gets {k.payout} points"
        rows.append(
            {
                **asdict(k),
                "note": note + _short_note(points, k.price),
                "too_poor": _too_poor(points, k.price),
                "token": uuid.uuid4().hex,
            }
        )
    return rows


def gift_rows(user, recipient):
    points = account(user).points
    counts = _owned(user)
    rows = []
    for k in rules.STICKERS:
        have = k.id in counts
        gets = f"{recipient.name} gets {k.payout} points"
        note = f"You own {counts[k.id]}. {gets}" if have else gets + _short_note(points, k.price)
        rows.append(
            {
                **asdict(k),
                "note": note,
                "have": have,
                "too_poor": not have and _too_poor(points, k.price),
            }
        )
    return rows


def stickers_on(kind, ids):
    """See social.stickers."""
    if not ids:
        return {}
    field = "post_id" if kind == "post" else "comment_id"
    counted = (
        StickerGift.objects.filter(**{f"{field}__in": ids})
        .values(field, "sticker")
        .annotate(n=Count("pk"))
    )
    by_target = {}
    for row in counted:
        by_target.setdefault(row[field], {})[row["sticker"]] = row["n"]
    return {
        target: [
            {**asdict(k), "count": found[k.id], "aria": f"{k.name}, {found[k.id]}"}
            for k in rules.STICKERS
            if k.id in found
        ]
        for target, found in by_target.items()
    }
