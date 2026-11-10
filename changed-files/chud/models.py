from django.conf import settings
from django.db import models
from django.db.models import F, Q

from catalogue.models import Media
from social.models import Post, PostComment


class ChudAccount(models.Model):
    """One member's balances, and the row every spend locks. A running total of the ledger, which
    is the truth: `manage.py verify_chud` checks the two agree. Written only by `chud.services`.

    `points` can go below zero: removing a log takes back what it earned even if that was spent.
    Spending is refused until the balance is positive again. XP can't, since nothing spends it.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE, related_name="chud"
    )
    points = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)
    # The highest level the member has been shown. Going back over it asks nothing new.
    peak_level = models.PositiveIntegerField(default=1)
    # A buddy they have reached and not yet answered the level-up sheet for.
    pending_buddy = models.CharField(max_length=20, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(xp__gte=0), name="chud_xp_not_negative"),
        ]

    def __str__(self):
        return f"{self.user}: {self.points} points, {self.xp} XP"


class ChudLedger(models.Model):
    """Append-only: every change to points or XP, signed. Balances can be rebuilt from it."""

    class Kind(models.TextChoices):
        EARN = "earn", "Logged"
        UNEARN = "unearn", "Log removed"
        BUY = "buy", "Bought a sticker"
        GIFT_SENT = "gift_sent", "Sent a sticker"
        GIFT_RECEIVED = "gift_received", "Received a sticker"
        BOUNTY_SET = "bounty_set", "Set a bounty"
        BOUNTY_REFUND = "bounty_refund", "Bounty cancelled"
        BOUNTY_COLLECT = "bounty_collect", "Collected a bounty"
        BOUNTY_BONUS = "bounty_bonus", "Taste bonus"
        BOUNTY_RETURN = "bounty_return", "Bounty taken back"
        ADJUST = "adjust", "Adjustment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chud_ledger"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    # What the member reads under Recent CHUD activity, as it stood at the time.
    text = models.CharField(max_length=300)
    points = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)
    counterparty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    media = models.ForeignKey(
        Media, null=True, blank=True, on_delete=models.SET_NULL, related_name="chud_ledger"
    )
    # Rows fold together when a member logs through a day, so this is where it landed.
    diary_entry = models.ForeignKey(
        "tracking.DiaryEntry", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    gift = models.ForeignKey(
        "chud.StickerGift", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    bounty = models.ForeignKey(
        "chud.Bounty", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    sticker = models.CharField(max_length=20, blank=True)
    # The award a removal takes back from.
    reverses = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reversals"
    )
    units = models.PositiveIntegerField(default=0)
    # Watch time as paid for, negative on a removal. Chud of the Week adds these up.
    minutes = models.IntegerField(default=0)
    watched_on = models.DateField(null=True, blank=True)
    # The same diary event or token twice is one row. Blank means there is nothing to repeat.
    key = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CHUD ledger row"
        verbose_name_plural = "CHUD ledger"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "key"], condition=~Q(key=""), name="chud_ledger_key_unique"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-id"]),
            models.Index(fields=["user", "media", "kind"]),
            models.Index(fields=["kind", "watched_on"]),
        ]

    def __str__(self):
        return f"{self.user}: {self.text}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("The CHUD ledger is append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("The CHUD ledger is append-only.")


class UserSticker(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chud_stickers"
    )
    sticker = models.CharField(max_length=20)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "sticker"], name="user_sticker_unique"),
        ]

    def __str__(self):
        return f"{self.user}: {self.count} {self.sticker}"


class StickerGift(models.Model):
    # Empty once the sender has deleted their account: the sticker stays on the post it was sent
    # to, because the recipient was paid for it and it is theirs, but it no longer has a name.
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stickers_sent",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stickers_received"
    )
    sticker = models.CharField(max_length=20)
    post = models.ForeignKey(
        Post, null=True, blank=True, on_delete=models.CASCADE, related_name="sticker_gifts"
    )
    comment = models.ForeignKey(
        PostComment, null=True, blank=True, on_delete=models.CASCADE, related_name="sticker_gifts"
    )
    # Nothing when it came out of the collection.
    price_paid = models.PositiveIntegerField(default=0)
    payout = models.PositiveIntegerField()
    token = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(post__isnull=False, comment__isnull=True))
                | Q(post__isnull=True, comment__isnull=False),
                name="sticker_gift_one_target",
            ),
            models.CheckConstraint(
                condition=~Q(sender=F("recipient")), name="sticker_gift_not_to_self"
            ),
            models.UniqueConstraint(
                fields=["sender", "token"], condition=~Q(token=""), name="sticker_gift_token_unique"
            ),
        ]

    def __str__(self):
        return f"{self.sender or 'A former member'} sent {self.recipient} {self.sticker}"


class Bounty(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COLLECTED = "collected", "Collected"
        CANCELLED = "cancelled", "Cancelled"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bounties_set"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bounties_on_them"
    )
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name="bounties")
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.OPEN)
    bonus_paid = models.BooleanField(default=False)
    token = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "bounties"
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=1), name="bounty_is_some_points"),
            models.CheckConstraint(condition=~Q(sender=F("recipient")), name="bounty_not_on_self"),
            models.UniqueConstraint(
                fields=["sender", "recipient", "media"],
                condition=Q(status="open"),
                name="bounty_one_open",
            ),
            models.UniqueConstraint(
                fields=["sender", "token"], condition=~Q(token=""), name="bounty_token_unique"
            ),
        ]
        indexes = [models.Index(fields=["recipient", "media", "status"])]

    def __str__(self):
        return f"{self.sender} on {self.recipient}: {self.amount} for {self.media}"


class WeeklyChudWinner(models.Model):
    """Chud of the Week. A tie is one row per winner. The latest week holds the crown."""

    # The Monday it started.
    week = models.DateField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chud_weeks_won"
    )
    minutes = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["week", "user"], name="weekly_chud_winner_unique"),
        ]
        indexes = [models.Index(fields=["-week"])]

    def __str__(self):
        return f"{self.user} won {self.week}"
