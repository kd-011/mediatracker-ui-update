"""Reading the social tables. The rule that matters is `visible_posts`: every screen and every
endpoint that shows a post starts from it, so there is one place that decides who may see what."""

from django.db.models import Avg, Count, Exists, F, IntegerField, OuterRef, Q, Sum
from django.shortcuts import get_object_or_404

from accounts.models import User
from tracking.models import DiaryEntry, ListEntry
from tracking.selectors import visible_entries

from .models import Follow, Post, PostComment, PostLike
from .stickers import stickers_on

FEED_PAGE = 10


def profile_stats(owner, viewer=None):
    """The Stats tab: what the diary says in totals. Diary privacy follows the library row's
    visibility, so rows behind a private entry count for the owner alone."""
    diary = DiaryEntry.objects.filter(user=owner)
    if viewer is not None and viewer.pk != owner.pk:
        shared = ListEntry.objects.filter(user=owner, visibility=User.Visibility.MEMBERS).values(
            "media"
        )
        diary = diary.filter(media_id__in=shared)
    spans = diary.filter(episode_from__isnull=False)
    avg = diary.filter(score__isnull=False).aggregate(a=Avg("score"))["a"]
    return {
        "movies": diary.filter(
            episode_from__isnull=True, episode_to__isnull=True
        ).count(),
        "episodes": spans.aggregate(
            n=Sum(F("episode_to") - F("episode_from") + 1, output_field=IntegerField())
        )["n"]
        or 0,
        "avg_score": round(avg, 1) if avg is not None else None,
    }


def favourites(owner, viewer=None):
    """The best-scored titles in the owner's library, twelve at most."""
    rows = visible_entries(owner, viewer or owner)
    return rows.filter(score__isnull=False).order_by("-score", "-updated_at", "-pk")[:12]


def visible_posts(viewer):
    """The posts `viewer` may see: all of their own, and other members' only when the post and
    the library entry it is about are both shared with members, the author is still active, and
    the title is not adult for someone who has not asked for adult titles.

    The entry is checked as well as the post because a card shows live data from the library:
    making an entry private later has to take its posts out of other people's feeds too."""
    entry_is_private = ListEntry.objects.filter(
        user=OuterRef("user"), media=OuterRef("media"), visibility=User.Visibility.PRIVATE
    )
    shared = Q(visibility=User.Visibility.MEMBERS, user__is_active=True) & ~Exists(entry_is_private)
    posts = Post.objects.filter(Q(user=viewer) | shared).select_related(
        "user", "media", "media__show"
    )
    if not viewer.show_adult:
        posts = posts.filter(media__is_adult=False)
    return posts


def with_counts(posts, viewer):
    return posts.annotate(
        n_likes=Count("likes", distinct=True),
        n_comments=Count("comments", distinct=True),
        liked=Exists(PostLike.objects.filter(post=OuterRef("pk"), user=viewer)),
    )


def following_ids(viewer):
    return Follow.objects.filter(follower=viewer).values("followee_id")


def feed_posts(viewer):
    """People you follow, and yourself, newest first."""
    mine_and_theirs = Q(user=viewer) | Q(user__in=following_ids(viewer))
    return with_counts(visible_posts(viewer).filter(mine_and_theirs), viewer).order_by("-pk")


def page_of(posts, before=None, size=FEED_PAGE):
    """(posts on this page, the cursor for the next one or None)."""
    if before:
        posts = posts.filter(pk__lt=before)
    found = list(posts[: size + 1])
    more = len(found) > size
    found = found[:size]
    return found, (found[-1].pk if more else None)


def posts_by(owner, viewer):
    return with_counts(visible_posts(viewer).filter(user=owner), viewer).order_by("-pk")


def post_for(viewer, pk):
    """404 for a post that does not exist and for one the viewer may not see, alike, so the
    answer never says which."""
    return get_object_or_404(with_counts(visible_posts(viewer), viewer), pk=pk)


def comments_for(post):
    """The post's comments, each with the stickers sent to it, in one query for all of them."""
    comments = list(PostComment.objects.filter(post=post).select_related("user"))
    gifts = stickers_on("comment", [c.pk for c in comments])
    for comment in comments:
        comment.stickers = gifts.get(comment.pk, [])
    return comments


def comment_for(viewer, pk):
    """A comment on a post the viewer may see."""
    return get_object_or_404(
        PostComment.objects.select_related("user", "post"),
        pk=pk,
        post__in=visible_posts(viewer).values("pk"),
    )


# People


def sharing(owner, viewer):
    """Whether `viewer` may see what `owner` has in the library and posts at all."""
    return owner.pk == viewer.pk or owner.default_visibility == User.Visibility.MEMBERS


def member_or_404(username):
    return get_object_or_404(User.objects.filter(is_active=True), username__iexact=username)


def people(viewer, query=""):
    found = User.objects.filter(is_active=True).exclude(pk=viewer.pk)
    query = query.strip()[:60]
    if query:
        found = found.filter(Q(username__icontains=query) | Q(display_name__icontains=query))
    return found.order_by("display_name", "username")


def followed_by(viewer, members):
    ids = [m.pk for m in members]
    return set(
        Follow.objects.filter(follower=viewer, followee_id__in=ids).values_list(
            "followee_id", flat=True
        )
    )


def follow_counts(owner):
    return {
        "followers": Follow.objects.filter(followee=owner).count(),
        "following": Follow.objects.filter(follower=owner).count(),
    }


def is_following(viewer, owner):
    return Follow.objects.filter(follower=viewer, followee=owner).exists()


NOTIFICATIONS_PER_SOURCE = 15


def notifications(user, limit=40):
    """Everything aimed at this member, newest first: follows, likes and comments on your posts,
    stickers sent to you, bounties set on you. Read straight from the live tables, so there is
    nothing to fan out or expire; seen-state lives in the session."""
    from django.urls import reverse

    from chud.models import Bounty, ChudLedger

    events = []
    for follow in (
        Follow.objects.filter(followee=user)
        .select_related("follower")
        .order_by("-created_at")[:NOTIFICATIONS_PER_SOURCE]
    ):
        events.append(
            {
                "when": follow.created_at,
                "text": f"{follow.follower.name} followed you",
                "url": reverse("social:profile", args=[follow.follower.username]),
            }
        )
    for like in (
        PostLike.objects.filter(post__user=user)
        .exclude(user=user)
        .select_related("user", "post", "post__media")
        .order_by("-created_at")[:NOTIFICATIONS_PER_SOURCE]
    ):
        events.append(
            {
                "when": like.created_at,
                "text": f"{like.user.name} liked your {like.post.media.title} post",
                "url": reverse("social:post", args=[like.post_id]),
            }
        )
    for comment in (
        PostComment.objects.filter(post__user=user)
        .exclude(user=user)
        .select_related("user", "post", "post__media")
        .order_by("-created_at")[:NOTIFICATIONS_PER_SOURCE]
    ):
        events.append(
            {
                "when": comment.created_at,
                "text": f"{comment.user.name} commented on your {comment.post.media.title} post",
                "url": reverse("social:post", args=[comment.post_id]),
            }
        )
    for row in (
        ChudLedger.objects.filter(user=user, kind=ChudLedger.Kind.GIFT_RECEIVED)
        .order_by("-created_at")[:NOTIFICATIONS_PER_SOURCE]
    ):
        events.append({"when": row.created_at, "text": row.text, "url": ""})
    for bounty in (
        Bounty.objects.filter(recipient=user, status=Bounty.Status.OPEN)
        .select_related("sender", "media")
        .order_by("-created_at")[:NOTIFICATIONS_PER_SOURCE]
    ):
        events.append(
            {
                "when": bounty.created_at,
                "text": f"{bounty.sender.name} set a bounty on {bounty.media.title}",
                "url": reverse("catalogue:title", args=[bounty.media_id]),
            }
        )
    events.sort(key=lambda e: e["when"], reverse=True)
    return events[:limit]
