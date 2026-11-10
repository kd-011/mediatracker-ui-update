import pytest
from django.urls import reverse

from social.models import Follow, PostComment, PostLike
from tracking import services as tracking

pytestmark = pytest.mark.django_db


def profile(client, user, name="profile"):
    return client.get(reverse(f"social:{name}", args=[user.username]))


def test_a_profile_shows_the_name_counts_and_a_follow_button(member_client, other):
    html = profile(member_client, other).content.decode()
    assert "Kev" in html and "@kev" in html
    assert reverse("social:follow", args=[other.username]) in html
    assert reverse("social:unfollow", args=[other.username]) not in html


def test_the_button_flips_once_you_follow(member_client, member, other):
    Follow.objects.create(follower=member, followee=other)
    html = profile(member_client, other).content.decode()
    assert reverse("social:unfollow", args=[other.username]) in html


def test_follower_and_following_counts(member_client, member, other, third):
    Follow.objects.create(follower=member, followee=other)
    Follow.objects.create(follower=third, followee=other)
    Follow.objects.create(follower=other, followee=member)
    html = profile(member_client, other).content.decode()
    assert 'class="me__stat-label">followers</span>' in html
    assert 'class="me__stat-label">following</span>' in html
    assert f'id="stat-followers-{other.username}"><span class="me__stat-value">2</span>' in html
    assert f'id="stat-following-{other.username}"><span class="me__stat-value">1</span>' in html


def test_your_own_profile_has_no_follow_button(member_client, member):
    html = member_client.get(reverse("accounts:me")).content.decode()
    assert reverse("social:follow", args=[member.username]) not in html


def test_your_own_profile_url_by_name_is_your_profile_too(member_client, member):
    html = profile(member_client, member).content.decode()
    assert f"@{member.username}" in html and "Posts" in html


def test_their_posts_are_listed_newest_first(
    member_client, other, make_movie, finish_movie, make_post
):
    first, second = make_movie("Dune: Part Two"), make_movie("Oppenheimer")
    for film, caption in ((first, "caption one"), (second, "caption two")):
        finish_movie(other, film)
        make_post(other, film, caption=caption)
    html = profile(member_client, other).content.decode()
    assert html.index('aria-label="Oppenheimer"') < html.index('aria-label="Dune: Part Two"')


def test_a_stranger_who_does_not_follow_can_still_read_a_public_profile(
    member_client, other, movie, finish_movie, make_post
):
    finish_movie(other, movie)
    make_post(other, movie)
    html = profile(member_client, other).content.decode()
    assert reverse("catalogue:title", args=[movie.pk]) in html


def test_their_library_page_uses_the_library_layout(
    member_client, other, movie, season, finish_movie, finish_season
):
    finish_movie(other, movie)
    finish_season(other, season)
    html = profile(member_client, other, "profile_library").content.decode()
    assert "Oppenheimer" in html and "Severance" in html
    assert "Kev" in html


def test_their_library_filters_work_on_their_own_url(
    member_client, other, movie, season, finish_movie, finish_season
):
    finish_movie(other, movie)
    finish_season(other, season)
    url = reverse("social:profile_library", args=[other.username])
    html = member_client.get(
        url, {"types": "movie"}, headers={"HX-Request": "true"}
    ).content.decode()
    assert "Oppenheimer" in html and "Severance" not in html


def test_their_watchlist_is_not_on_their_profile(member_client, other, movie):
    tracking.set_watchlist(other, movie, True)
    html = profile(member_client, other).content.decode()
    assert "Oppenheimer" not in html
    assert reverse("social:profile_library", args=[other.username]) in html


def test_an_unknown_or_deactivated_member_is_a_404(member_client, other):
    assert member_client.get(reverse("social:profile", args=["nobody"])).status_code == 404
    other.is_active = False
    other.save()
    assert profile(member_client, other).status_code == 404


def test_your_own_profile_lists_your_posts_and_the_visibility_setting(
    member_client, member, movie, finish_movie, make_post
):
    finish_movie(member, movie)
    make_post(member, movie)
    html = member_client.get(reverse("accounts:me")).content.decode()
    assert reverse("catalogue:title", args=[movie.pk]) in html
    settings_html = member_client.get(reverse("member:settings")).content.decode()
    assert "default_visibility" in settings_html


# People


def test_the_directory_lists_members_with_follow_buttons(member_client, other, third):
    html = member_client.get(reverse("social:people")).content.decode()
    assert "Kev" in html and "Jimmy" in html
    assert reverse("social:follow", args=[other.username]) in html


def test_the_directory_leaves_out_you_and_the_deactivated(member_client, member, other, third):
    third.is_active = False
    third.save()
    html = member_client.get(reverse("social:people")).content.decode()
    assert "Kev" in html and "Jimmy" not in html
    assert reverse("social:follow", args=[member.username]) not in html


def test_search_by_username_or_display_name_any_case(member_client, other, third):
    for q in ("KEV", "kev", "Jim", "jimmy"):
        html = member_client.get(reverse("social:people"), {"q": q}).content.decode()
        expected = "Kev" if q.lower().startswith("k") else "Jimmy"
        unexpected = "Jimmy" if expected == "Kev" else "Kev"
        assert expected in html and unexpected not in html


def test_search_with_no_match_says_so(member_client, other):
    assert "No one" in member_client.get(reverse("social:people"), {"q": "zzz"}).content.decode()


def test_the_header_search_finds_members_too(member_client, other):
    html = member_client.get(reverse("core:search"), {"q": "kev"}).content.decode()
    assert reverse("social:profile", args=[other.username]) in html


def test_a_search_for_a_percent_sign_is_a_literal(member_client, other):
    html = member_client.get(reverse("social:people"), {"q": "%"}).content.decode()
    assert "Kev" not in html


def test_the_directory_needs_a_login():
    from django.test import Client

    assert Client().get(reverse("social:people")).status_code == 302


def test_hide_comments_answers_with_the_closed_panel(
    member_client, member, movie, finish_movie, make_post
):
    finish_movie(member, movie)
    post = make_post(member, movie)
    response = member_client.get(
        reverse("social:comments", args=[post.pk]), {"closed": "1"}, headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert f'id="post-comments-{post.pk}"' in html and "Add a comment" not in html


def test_older_posts_are_reachable_from_a_profile(
    member_client, other, make_movie, finish_movie, make_post
):
    for i in range(13):
        film = make_movie(f"Film {i}")
        finish_movie(other, film)
        make_post(other, film, caption=f"post {i:02d}")
    first = profile(member_client, other).content.decode()
    posts = first.split('data-panel="posts"')[1].split('data-panel="stats"')[0]
    assert 'aria-label="Film 12"' in posts and 'aria-label="Film 2"' not in posts
    import re

    nxt = re.search(r'hx-get="([^"]*/posts/\?before=[^"]*)"', first).group(1).replace("&amp;", "&")
    second = member_client.get(nxt, headers={"HX-Request": "true"}).content.decode()
    assert 'aria-label="Film 2"' in second and "Film 12" not in second
    assert "before=" not in second


def test_a_private_profile_has_no_older_posts_endpoint(
    member, other, other_client, movie, finish_movie, make_post
):
    from social import services as social

    finish_movie(member, movie)
    make_post(member, movie)
    social.set_account_visibility(member, "private")
    assert (
        other_client.get(reverse("social:profile_posts", args=[member.username])).status_code == 404
    )


def test_another_members_library_varies_on_htmx_so_back_never_shows_a_fragment(
    member_client, other
):
    response = member_client.get(reverse("social:profile_library", args=[other.username]))
    vary = response.headers.get("Vary", "")
    assert "HX-Request" in vary and "HX-History-Restore-Request" in vary


def test_slide_dots_are_44px_wide():
    from pathlib import Path

    css = (Path(__file__).resolve().parents[2] / "core/static/core/css/app.css").read_text()
    assert ".post__dot { width: 44px;" in css


def test_notifications_list_follows_likes_and_comments(member, member_client, other, movie, finish_movie, make_post):
    Follow.objects.create(follower=other, followee=member)
    finish_movie(member, movie)
    post = make_post(member, movie)
    PostLike.objects.create(post=post, user=other)
    PostComment.objects.create(post=post, user=other, body="stunner")
    html = member_client.get(reverse("social:notifications")).text
    assert f"{other.name} followed you" in html
    assert f"{other.name} liked your {movie.title} post" in html
    assert f"{other.name} commented on your {movie.title} post" in html
    assert reverse("social:notifications") in member_client.get(reverse("accounts:me")).text
