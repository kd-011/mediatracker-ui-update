"""What a member can do to their own account: a picture, a password, and leaving.

Leaving is the one that matters. Everything the member owns goes. What they gave to other people is
dealt with one kind at a time, below, and written down in the README so nobody is surprised.
"""

import io
import re
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from PIL import Image, ImageOps, UnidentifiedImageError

from accounts.models import User
from accounts.services import end_sessions
from chud import services as chud
from chud.models import Bounty, ChudLedger

AVATAR_SIZE = 256
AVATAR_FORMATS = {"PNG", "JPEG", "WEBP"}
AVATAR_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}\.webp$")


class MemberError(Exception):
    """Something the member did that we can say plainly. The message is safe to show."""


class AvatarError(MemberError):
    pass


# A picture


def avatar_path(name):
    """Where an avatar file lives, or None for a name we did not make."""
    return Path(settings.AVATAR_DIR) / name if AVATAR_NAME.match(name or "") else None


def _remove_file(name):
    path = avatar_path(name)
    if path is not None:
        path.unlink(missing_ok=True)


def _encode(upload):
    """The picture as a 256 pixel square WebP, or an AvatarError. Nothing from the upload except
    its pixels survives: no metadata, no name, no original format."""
    if upload.size > settings.AVATAR_MAX_BYTES:
        mb = settings.AVATAR_MAX_BYTES // (1024 * 1024)
        raise AvatarError(f"That picture is over {mb} MB. Pick a smaller one.")
    raw = upload.read(settings.AVATAR_MAX_BYTES + 1)
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in AVATAR_FORMATS:
                raise AvatarError("Use a PNG, JPEG or WebP picture.")
            # The header says how big it claims to be, before anything is decoded.
            if image.width * image.height > settings.AVATAR_MAX_PIXELS:
                raise AvatarError("That picture is far too large in pixels. Pick a smaller one.")
            image = ImageOps.exif_transpose(image)
            image = ImageOps.fit(image.convert("RGBA"), (AVATAR_SIZE, AVATAR_SIZE))
            out = io.BytesIO()
            image.save(out, "WEBP", quality=85)
    except AvatarError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise AvatarError("That doesn't look like a picture we can read.") from None
    return out.getvalue()


def set_avatar(user, upload):
    data = _encode(upload)
    directory = Path(settings.AVATAR_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{user.pk}-{secrets.token_hex(8)}.webp"
    (directory / name).write_bytes(data)
    old = user.avatar_path
    user.avatar_path = name
    user.save(update_fields=["avatar_path", "updated_at"])
    _remove_file(old)


def remove_avatar(user):
    old = user.avatar_path
    user.avatar_path = ""
    user.save(update_fields=["avatar_path", "updated_at"])
    _remove_file(old)


# Stock avatars: bundled art a member can pick instead of uploading. The path keeps the
# "stock:" prefix so a stored name can never collide with an upload, and the SVG itself is
# served straight from the repo by `member:stock_avatar`.

STOCK_AVATARS = ("sprout", "bolt", "ghost", "heart", "star", "moon")


def stock_avatar_file(key):
    base = Path(__file__).resolve().parent / "static" / "member" / "avatars"
    path = base / f"{key}.svg"
    return path if key in STOCK_AVATARS and path.is_file() else None


def set_stock_avatar(user, key):
    if key not in STOCK_AVATARS:
        raise AvatarError("Pick one of the available avatars.")
    old = user.avatar_path
    user.avatar_path = f"stock:{key}"
    user.save(update_fields=["avatar_path", "updated_at"])
    _remove_file(old)


# A password


def change_password(user, new):
    """Sets it and ends every session, this one included: the caller signs the member back in
    here, so a phone that was lost or borrowed is signed out."""
    validate_password(new, user)
    user.set_password(new)
    user.save(update_fields=["password", "updated_at"])
    end_sessions(user)


# Leaving


class CannotLeave(MemberError):
    pass


def check_can_leave(user):
    if (
        user.is_admin
        and not User.objects.filter(is_admin=True, is_active=True).exclude(pk=user.pk).exists()
    ):
        raise CannotLeave(
            "You are the only admin. Make another member an admin in /admin/ first, "
            "or nobody will be able to invite anyone."
        )


def _scrub_names(user):
    """Other members' CHUD ledger rows name this member in their text ("Maya sent you Cooked").
    Their points stay, since they were paid; the name goes. The ledger is append-only through
    the model, so this rewrites only the words, in place, and touches no number."""
    names = sorted({n for n in (user.name, user.username) if n}, key=len, reverse=True)
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in names) + r")\b", re.IGNORECASE)
    rows = list(ChudLedger.objects.filter(counterparty=user))
    for row in rows:
        row.text = pattern.sub("Someone", row.text)
    ChudLedger.objects.bulk_update(rows, ["text"], batch_size=500)


def _refund_open_bounties(user):
    """Friends who put points on this member finishing something get them back in full. The
    ones this member set have no one left to refund and go with the account."""
    for bounty in Bounty.objects.filter(recipient=user, status=Bounty.Status.OPEN).select_related(
        "sender"
    ):
        chud.cancel_bounty(bounty, bounty.sender)


def _upload_files(user):
    from imports.models import ImportJob

    return [j.file_path for j in ImportJob.objects.filter(user=user).exclude(file_path="")]


def _delete_rows(user):
    _refund_open_bounties(user)
    _scrub_names(user)
    end_sessions(user)
    # Everything else the member owns is a foreign key to the user and goes with it: library,
    # diary, episode scores, hold spells, tags, follows both ways, posts with their likes,
    # comments and stickers, the member's own likes and comments elsewhere, CHUD account, ledger,
    # owned stickers, bounties they set, crowns, import jobs and the codes they made. A sticker
    # they sent stays on the friend's post with no sender (StickerGift.sender is SET_NULL).
    User.objects.filter(pk=user.pk).delete()


def delete_account(user):
    """Remove the member and all they own, or do nothing at all. Files go after the rows, so a
    failure part way leaves the account whole."""
    check_can_leave(user)
    avatar, uploads = user.avatar_path, _upload_files(user)
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        check_can_leave(locked)
        _delete_rows(locked)
    _remove_file(avatar)
    for path in uploads:
        target = Path(path)
        root = Path(settings.IMPORT_UPLOAD_DIR).resolve()
        if root in target.resolve().parents:
            target.unlink(missing_ok=True)
