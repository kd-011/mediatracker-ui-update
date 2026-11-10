"""Private data never crosses between members."""

import re

import pytest
from django.test import Client
from django.urls import reverse

from social import services as social
from social.models import Follow, Post, PostComment
from social.tests.conftest import CAPTION, SPOILER
from tracking import services as tracking
from tracking.models import ListEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def secret(member, other, movie, finish_movie, make_post):
    """Maya posts a movie, then goes private. Kev follows her."""
    finish_movie(member, movie)
    post = make_post(member, movie, spoiler_review=SPOILER)
    Follow.objects.create(follower=other, followee=member)
    social.set_account_visibility(member, "private")
    post.refresh_from_db()
    return post


def test_going_private_flips_the_posts_and_the_library(secret, member):
    assert secret.visibility == "private"
    assert member.default_visibility == "private"
    assert ListEntry.objects.get(user=member).visibility == "private"


def test_going_back_flips_them_back(secret, member):
    social.set_account_visibility(member, "members")
    secret.refresh_from_db()
    assert secret.visibility == "members"
    assert ListEntry.objects.get(user=member).visibility == "members"


def test_new_entries_and_posts_of_a_private_member_start_private(
    member, make_movie, finish_movie, make_post
):
    social.set_account_visibility(member, "private")
    film = make_movie("Dune: Part Two")
    finish_movie(member, film)
    assert make_post(member, film).visibility == "private"


def test_a_private_post_is_not_in_a_followers_feed(secret, other_client):
    html = other_client.get(reverse("core:feed")).content.decode()
    assert CAPTION not in html


@pytest.mark.parametrize(
    ("name", "method"),
    [
        ("post", "get"),
        ("spoiler", "get"),
        ("comments", "get"),
        ("like", "post"),
        ("comment_add", "post"),
        ("post_edit", "get"),
        ("post_delete", "post"),
    ],
)
def test_every_post_endpoint_says_404_for_a_private_post(secret, other_client, other, name, method):
    target = reverse(f"social:{name}", args=[secret.pk])
    response = getattr(other_client, method)(target, {"body": "hi", "on": "1"})
    assert response.status_code == 404
    assert not secret.likes.exists() and not secret.comments.exists()


def test_a_private_comments_spoiler_endpoint_is_404_too(secret, other_client, member):
    comment = PostComment.objects.create(post=secret, user=member, body="x", is_spoiler=True)
    assert other_client.get(reverse("social:comment_spoiler", args=[comment.pk])).status_code == 404
    assert other_client.post(reverse("social:comment_delete", args=[comment.pk])).status_code == 404
    assert PostComment.objects.filter(pk=comment.pk).exists()


def test_the_owner_still_sees_their_private_post(secret, member_client):
    assert member_client.get(reverse("social:post", args=[secret.pk])).status_code == 200
    assert CAPTION in member_client.get(reverse("core:feed")).content.decode()


def test_a_private_profile_shows_a_notice_and_nothing_else(secret, other_client, member):
    html = other_client.get(reverse("social:profile", args=[member.username])).content.decode()
    assert "private" in html.lower()
    assert CAPTION not in html and "Oppenheimer" not in html
    lib = other_client.get(reverse("social:profile_library", args=[member.username]))
    assert "Oppenheimer" not in lib.content.decode()


def test_private_entries_are_missing_from_a_members_library_but_public_ones_show(
    member, other, other_client, movie, season, finish_movie, finish_season
):
    finish_movie(member, movie)
    finish_season(member, season)
    ListEntry.objects.filter(user=member, media=movie).update(visibility="private")
    html = other_client.get(
        reverse("social:profile_library", args=[member.username])
    ).content.decode()
    assert "Oppenheimer" not in html
    assert "Severance" in html


def test_a_private_entry_hides_the_post_about_it(
    member, other, other_client, movie, finish_movie, make_post
):
    finish_movie(member, movie)
    make_post(member, movie)
    Follow.objects.create(follower=other, followee=member)
    ListEntry.objects.filter(user=member).update(visibility="private")
    assert CAPTION not in other_client.get(reverse("core:feed")).content.decode()


def test_a_private_title_is_not_in_their_public_stats_or_favourites(
    member, other, other_client, movie
):
    tracking.add_diary_row(member, movie, score=9)
    url = reverse("social:profile", args=[member.username])
    assert reverse("catalogue:title", args=[movie.pk]) in other_client.get(url).content.decode()
    ListEntry.objects.filter(user=member).update(visibility="private")
    html = other_client.get(url).content.decode()
    assert reverse("catalogue:title", args=[movie.pk]) not in html
    assert "<span>Movies</span><b>0</b>" in html


def test_a_members_own_library_ignores_visibility(member_client, member, movie, finish_movie):
    finish_movie(member, movie)
    ListEntry.objects.filter(user=member).update(visibility="private")
    assert "Oppenheimer" in member_client.get(reverse("core:library")).content.decode()


def test_the_visibility_setting_is_the_members_own(member_client, member, other):
    member_client.post(reverse("social:visibility"), {"visibility": "private"})
    member.refresh_from_db()
    other.refresh_from_db()
    assert member.default_visibility == "private"
    assert other.default_visibility == "members"
    assert (
        member_client.post(reverse("social:visibility"), {"visibility": "everyone"}).status_code
        == 400
    )


def test_posting_a_private_entry_stays_private_to_the_author(
    member, member_client, movie, finish_movie
):
    finish_movie(member, movie)
    ListEntry.objects.filter(user=member).update(visibility="private")
    social.create_post(member, movie, "finished", caption="x")
    assert Post.objects.get().visibility == "private"


def test_no_page_of_another_member_leaks_the_private_title_name(secret, other_client, member):
    pages = [
        reverse("core:feed"),
        reverse("social:people"),
        reverse("social:profile", args=[member.username]),
        reverse("social:profile_library", args=[member.username]),
    ]
    for page in pages:
        assert "Oppenheimer" not in other_client.get(page).content.decode(), page
    # Home is left out on purpose: its carousels list the shared catalogue, which has the title
    # in it whoever logged it. Who logged it is what stays private, and the popularity count
    # already ignores private entries (test_screens.py).
    # And an unauthenticated visitor gets nothing at all.
    for page in pages:
        assert Client().get(page).status_code == 302


def test_the_comments_list_hides_nothing_from_the_author_but_requires_visibility(
    secret, member_client
):
    html = member_client.get(
        reverse("social:comments", args=[secret.pk]), headers={"HX-Request": "true"}
    )
    assert html.status_code == 200
    assert re.search(r"comment", html.content.decode(), re.I)


def test_a_private_post_stays_hidden_even_when_the_entry_is_shared(
    member, other, other_client, movie, finish_movie, make_post
):
    finish_movie(member, movie)
    post = make_post(member, movie)
    Follow.objects.create(follower=other, followee=member)
    Post.objects.filter(pk=post.pk).update(visibility="private")
    assert CAPTION not in other_client.get(reverse("core:feed")).content.decode()
    assert other_client.get(reverse("social:post", args=[post.pk])).status_code == 404
    assert (
        CAPTION
        not in other_client.get(reverse("social:profile", args=[member.username])).content.decode()
    )
