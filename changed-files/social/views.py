"""Follows, the feed, posts, likes, comments and profiles.

Writes answer with out-of-band fragments for the parts of the page they changed, as tracking's do,
so they go through the same offline queue in app.js. Every post and comment is looked up through
`selectors.visible_posts`: a post the viewer may not see is a 404 on every route.
"""

import uuid

from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.vary import vary_on_headers

from catalogue.models import Media
from chud import selectors as chud_selectors
from tracking import selectors as tracking_selectors
from tracking import services as tracking
from tracking.views import _changed as tracking_changed
from tracking.views import _day_of, render_library

from . import cards, selectors, services
from .services import SocialError


def _refused(exc):
    return HttpResponse(str(exc), status=400, content_type="text/plain; charset=utf-8")


def _toast(response, value, **extra):
    import json

    events = json.loads(response.get("HX-Trigger", "{}"))
    events["toast"] = {"value": value, **extra}
    response["HX-Trigger"] = json.dumps(events)
    return response


def _card(request, post):
    return cards.build_cards([post], request.user)[0]


# Feed


@require_GET
def feed(request):
    viewer = request.user
    try:
        before = int(request.GET.get("before", 0)) or None
    except ValueError:
        before = None
    posts, cursor = selectors.page_of(selectors.feed_posts(viewer), before)
    context = {
        "cards": cards.build_cards(posts, viewer),
        "next_url": f"{reverse('core:feed')}?before={cursor}" if cursor else "",
    }
    if before:
        return render(request, "social/_feed_page.html", context)
    context["following"] = selectors.following_ids(viewer).exists()
    return render(request, "social/feed.html", context)


# People and profiles


@require_GET
def people(request):
    query = request.GET.get("q", "").strip()[:60]
    members = list(selectors.people(request.user, query))
    context = {
        "members": members,
        "following": selectors.followed_by(request.user, members),
        "query": query,
    }
    return render(request, "social/people.html", context)


def _posts_url(owner, cursor):
    return (
        f"{reverse('social:profile_posts', args=[owner.username])}?before={cursor}"
        if cursor
        else ""
    )


def profile_context(request, owner):
    viewer = request.user
    sharing = selectors.sharing(owner, viewer)
    context = {
        "owner": owner,
        "is_self": owner.pk == viewer.pk,
        "sharing": sharing,
        "follows": selectors.follow_counts(owner),
        "following": selectors.is_following(viewer, owner) if owner.pk != viewer.pk else False,
    }
    if sharing:
        posts, cursor = selectors.page_of(selectors.posts_by(owner, viewer), None)
        context.update(
            next_url=_posts_url(owner, cursor),
            counts=tracking_selectors.counts(owner, viewer),
            watchlist=tracking_selectors.watchlist(owner, viewer),
            cards=cards.build_cards(posts, viewer),
            chud=chud_selectors.profile(owner, viewer),
            stats=selectors.profile_stats(owner, viewer),
            favourites=selectors.favourites(owner, viewer),
        )
    return context


@require_GET
def profile(request, username):
    owner = selectors.member_or_404(username)
    return render(request, "social/profile.html", profile_context(request, owner))


@require_GET
def profile_posts(request, username):
    """The next page of a member's posts, for the loader at the foot of their profile."""
    owner = selectors.member_or_404(username)
    if not selectors.sharing(owner, request.user):
        raise Http404
    try:
        before = int(request.GET.get("before", 0)) or None
    except ValueError:
        before = None
    posts, cursor = selectors.page_of(selectors.posts_by(owner, request.user), before)
    cards_ = cards.build_cards(posts, request.user)
    context = {
        "cards": cards_,
        "next_url": _posts_url(owner, cursor),
    }
    if request.GET.get("view") == "grid":
        return render(request, "social/_post_grid.html", context)
    return render(request, "social/_feed_page.html", context)


@require_GET
@vary_on_headers("HX-Request", "HX-History-Restore-Request")
def profile_library(request, username):
    owner = selectors.member_or_404(username)
    if not selectors.sharing(owner, request.user):
        return render(request, "social/profile.html", profile_context(request, owner))
    return render_library(request, owner, "social/library.html")


def _follow_fragments(request, target):
    context = {
        "target": target,
        "following": selectors.is_following(request.user, target),
        "follows": selectors.follow_counts(target),
        "oob": True,
    }
    return render(request, "social/_follow_changed.html", context)


@require_POST
def follow(request, username):
    target = selectors.member_or_404(username)
    try:
        services.follow(request.user, target)
    except SocialError as exc:
        return _refused(exc)
    return _follow_fragments(request, target)


@require_POST
def unfollow(request, username):
    target = selectors.member_or_404(username)
    services.unfollow(request.user, target)
    return _follow_fragments(request, target)


@require_POST
def visibility(request):
    try:
        services.set_account_visibility(request.user, request.POST.get("visibility", ""))
    except SocialError as exc:
        return _refused(exc)
    request.user.refresh_from_db()
    response = render(request, "social/_visibility.html", {"oob": True})
    return _toast(response, "Saved")


# Posting


@require_POST
def post_create(request, pk):
    media = get_object_or_404(Media.objects.select_related("show").visible_to(request.user), pk=pk)
    user = request.user
    before = tracking_selectors.entry_for(user, media)
    before_status = before.status if before else ""
    wanted = request.POST.get("score", "").strip()
    try:
        with transaction.atomic():
            if wanted.lstrip("-").isdigit():
                score = int(wanted)
                if score != tracking_selectors.score_to_rate(user, media):
                    tracking.rate(user, media, score, on=_day_of(request))
            post = services.create_post(
                user,
                media,
                request.POST.get("outcome", ""),
                caption=request.POST.get("caption", ""),
                spoiler_review=request.POST.get("spoiler_review", ""),
                token=request.POST.get("token", ""),
            )
    except tracking.ReplaceNeeded:
        return _refused(
            "Changing the season score clears your episode scores. Rate it from the title page."
        )
    except (SocialError, tracking.DiaryError) as exc:
        return _refused(exc)
    toast = {"value": "Posted", "undo": reverse("social:post_delete", args=[post.pk])}
    return tracking_changed(request, media, before_status, toast=toast, close=True, all_=True)


def _visible_post(request, pk):
    return selectors.post_for(request.user, pk)


@require_GET
def post_detail(request, pk):
    post = _visible_post(request, pk)
    card = _card(request, post)
    context = {
        "card": card,
        "comments": selectors.comments_for(post),
        "open": True,
        "token": uuid.uuid4().hex,
    }
    return render(request, "social/post.html", context)


def _own_post(request, pk):
    post = _visible_post(request, pk)
    if post.user_id != request.user.pk:
        return post, HttpResponseForbidden("That isn't your post.")
    return post, None


def post_edit(request, pk):
    post, refused = _own_post(request, pk)
    if refused:
        return refused
    if request.method != "POST":
        return render(
            request, "social/sheets/edit_post.html", {"post": post, "card": _card(request, post)}
        )
    try:
        services.edit_post(
            post,
            caption=request.POST.get("caption", ""),
            spoiler_review=request.POST.get("spoiler_review", ""),
        )
    except SocialError as exc:
        return _refused(exc)
    post = selectors.post_for(request.user, pk)
    response = render(request, "social/_card_changed.html", {"card": _card(request, post)})
    response["HX-Trigger"] = '{"sheet-close": true}'
    return _toast(response, "Post updated")


@require_POST
def post_delete(request, pk):
    post, refused = _own_post(request, pk)
    if refused:
        return refused
    post_pk = post.pk
    services.delete_post(post)
    response = render(request, "social/_card_gone.html", {"pk": post_pk})
    return _toast(response, "Post deleted")


# Likes


@require_POST
def like(request, pk):
    post = _visible_post(request, pk)
    services.set_like(post, request.user, request.POST.get("on") == "1")
    post = selectors.post_for(request.user, pk)
    return render(request, "social/_actions_changed.html", {"card": _card(request, post)})


# Comments


def _comments_response(request, post, template="social/_comments.html", status=200):
    context = {
        "post": post,
        "comments": selectors.comments_for(post),
        "open": True,
        "token": uuid.uuid4().hex,
    }
    return render(request, template, context, status=status)


@require_GET
def comments(request, pk):
    post = _visible_post(request, pk)
    if request.GET.get("closed") == "1":
        return render(request, "social/_comments.html", {"post": post, "open": False})
    return _comments_response(request, post)


@require_POST
def comment_add(request, pk):
    post = _visible_post(request, pk)
    try:
        services.add_comment(
            post,
            request.user,
            request.POST.get("body", ""),
            request.POST.get("is_spoiler") == "on",
            token=request.POST.get("token", ""),
        )
    except SocialError as exc:
        return _refused(exc)
    post = selectors.post_for(request.user, pk)
    context = {
        "card": _card(request, post),
        "post": post,
        "comments": selectors.comments_for(post),
        "open": True,
        "token": uuid.uuid4().hex,
    }
    return render(request, "social/_comment_added.html", context)


@require_POST
def comment_delete(request, pk):
    comment = selectors.comment_for(request.user, pk)
    post_pk = comment.post_id
    if request.user.pk not in (comment.user_id, comment.post.user_id):
        return HttpResponseForbidden("That isn't your comment.")
    services.delete_comment(comment)
    post = selectors.post_for(request.user, post_pk)
    context = {
        "card": _card(request, post),
        "post": post,
        "comments": selectors.comments_for(post),
        "open": True,
        "token": uuid.uuid4().hex,
    }
    return render(request, "social/_comment_added.html", context)


# Spoilers: the only place the text is ever sent


@require_GET
def spoiler(request, pk):
    post = _visible_post(request, pk)
    if request.GET.get("closed") == "1":
        return render(request, "social/_spoiler_closed.html", {"post": post})
    return render(request, "social/_spoiler.html", _spoiler_context(post))


def _spoiler_context(post):
    return {"post": post, "notes": tracking_selectors.episode_notes(post.user, post.media)}


@require_GET
def comment_spoiler(request, pk):
    comment = selectors.comment_for(request.user, pk)
    if not comment.is_spoiler:
        raise Http404
    return render(request, "social/_comment_text.html", {"comment": comment})


@require_GET
def notifications(request):
    """The bell's page. Unseen is what arrived after your last visit here, then the visit counts
    as seen."""
    from django.utils.dateparse import parse_datetime
    from django.utils.timezone import now

    events = selectors.notifications(request.user)
    seen = parse_datetime(request.session.get("notif_seen") or "")
    unseen = len(events) if seen is None else sum(1 for e in events if e["when"] > seen)
    request.session["notif_seen"] = now().isoformat()
    return render(request, "social/notifications.html", {"events": events, "unseen": unseen})
