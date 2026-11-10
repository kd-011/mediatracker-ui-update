"""What a member sees and presses. Writes go through tracking's endpoints and answer with
out-of-band fragments, so these read the responses the way the page would."""

import json
import re
from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Media, Show
from tracking import services
from tracking.models import DiaryEntry, ListEntry, Status

pytestmark = pytest.mark.django_db

DAY = date(2026, 10, 24)


def url(name, media):
    return reverse(f"tracking:{name}", args=[media.pk])


def post(client, name, media, *args, **data):
    target = reverse(f"tracking:{name}", args=[media.pk, *args])
    return client.post(target, data, headers={"HX-Request": "true"})


def body(response):
    return response.content.decode()


def trigger(response):
    return json.loads(response.headers.get("HX-Trigger", "{}"))


# Every write endpoint


WRITES = ["log", "bulk", "rate", "status", "watchlist", "undo", "rewatch"]


@pytest.mark.parametrize("name", WRITES)
def test_writes_need_a_login(movie, name):
    response = Client().post(url(name, movie), {"score": 5, "status": "on_hold", "to": 2})
    assert response.status_code == 302
    assert not DiaryEntry.objects.exists()
    assert not ListEntry.objects.exists()


@pytest.mark.parametrize("name", ["log", "status", "watchlist", "undo", "rewatch"])
def test_writes_are_post_only(member_client, movie, name):
    assert member_client.get(url(name, movie)).status_code == 405
    assert not DiaryEntry.objects.exists()


@pytest.mark.parametrize("name", WRITES)
def test_writes_need_a_csrf_token(member, movie, name):
    client = Client(enforce_csrf_checks=True)
    client.force_login(member)
    assert client.post(url(name, movie), {"score": 5}).status_code == 403
    assert not DiaryEntry.objects.exists()


@pytest.mark.parametrize("name", WRITES)
def test_adult_titles_are_a_404_unless_opted_in(member_client, name):
    grown = Media.objects.create(type="movie", title="Grown", metadata_source="mal", is_adult=True)
    assert post(member_client, name, grown, score=5, status="on_hold", to=2).status_code == 404
    assert not DiaryEntry.objects.exists()


# +1 and logging


def test_plus_one_answers_with_the_new_progress_and_an_undo(member, member_client, season):
    services.log_up_to(member, season, to=8, on=DAY)
    response = post(member_client, "log", season, n=9, source="currently")
    html = body(response)
    assert response.status_code == 200
    assert f'id="entry-{season.pk}-info"' in html
    assert "hx-swap-oob" in html
    assert "Next: Episode 10" in html
    assert "9 / 10" in html
    toast = trigger(response)["toast"]
    assert toast["value"] == "Episode 9 logged"
    assert toast["undo"] == url("undo", season)
    assert toast["n"] == 9


def test_plus_one_naming_a_unit_twice_counts_once(member_client, season):
    post(member_client, "log", season, n=1, source="currently")
    post(member_client, "log", season, n=1, source="currently")
    assert ListEntry.objects.get().progress == 1


def test_plus_one_uses_the_date_the_phone_sent(member_client, season):
    yesterday = timezone.localdate() - timedelta(days=1)
    post(member_client, "log", season, n=1, local_date=yesterday.isoformat())
    assert DiaryEntry.objects.get().watched_on == yesterday


@pytest.mark.parametrize(
    "bad",
    ["2999-01-01", "garbage", "1999-01-01", ""],
)
def test_a_date_off_by_more_than_a_queued_write_could_be_falls_back_to_today(
    member_client, season, bad
):
    post(member_client, "log", season, n=1, local_date=bad)
    assert DiaryEntry.objects.get().watched_on == timezone.localdate()


def test_a_queued_write_keeps_the_day_it_was_made(member_client, season):
    # Offline for a week on holiday, then back on Wi-Fi.
    made = timezone.localdate() - timedelta(days=7)
    post(member_client, "log", season, n=1, local_date=made.isoformat())
    assert DiaryEntry.objects.get().watched_on == made


def test_completing_a_season_raises_post_or_skip_and_removes_the_row(member, member_client, season):
    services.log_up_to(member, season, to=9, on=DAY)
    html = body(post(member_client, "log", season, n=10, source="currently"))
    assert f'id="entry-{season.pk}"' in html
    assert 'hx-swap-oob="delete"' in html
    assert 'id="sheet-host"' in html
    assert "data-sheet" in html
    # M3: the last episode is asked about first, as every episode is. Then comes the prompt.
    html = body(post(member_client, "episode_score", season, 10, finished="1", skip="1"))
    assert "You finished Severance, Season 1" in html


def test_logging_a_movie_raises_post_or_skip(member_client, movie):
    html = body(post(member_client, "log", movie, source="title"))
    assert "You finished Oppenheimer" in html
    assert "data-sheet" in html
    assert f'id="title-actions-{movie.pk}"' in html


def test_a_step_that_does_not_complete_raises_no_prompt(member_client, season):
    html = body(post(member_client, "log", season, n=1, source="currently"))
    # M3: it does ask about the episode. See test_episode_screens.py.
    assert "You finished" not in html


def test_the_post_button_is_live_and_skip_still_rates(member_client, movie):
    # M2 left Post as a disabled stub. M5's composer replaces it: see social/tests/test_composer.py.
    html = body(post(member_client, "log", movie))
    assert not re.search(r"<button[^>]*disabled[^>]*>\s*Post\s*</button>", html)
    assert "Posting arrives with the feed" not in html
    assert re.search(r"<button[^>]*>\s*Post\s*</button>", html)
    assert re.search(r'formaction="[^"]*/rate/"[^>]*>\s*Skip', html)


def test_skip_keeps_the_rating_chosen_in_the_prompt(member_client, movie):
    post(member_client, "log", movie)
    response = post(member_client, "rate", movie, score=9)
    assert ListEntry.objects.get().score == 9
    assert "sheet-close" in trigger(response)


def test_skip_with_no_rating_leaves_it_unrated_and_writes_no_rows(member_client, movie):
    post(member_client, "log", movie)
    post(member_client, "rate", movie, score="", keep_unrated="1")
    assert ListEntry.objects.get().score is None
    assert DiaryEntry.objects.count() == 1


def test_a_bad_unit_number_is_a_readable_400(member_client, season):
    response = post(member_client, "log", season, n="abc")
    assert response.status_code == 400
    assert not DiaryEntry.objects.exists()


def test_a_unit_past_the_end_of_a_finished_season_is_a_no_op_not_an_error(
    member, member_client, season
):
    # The second tap of a double tap on the final episode.
    services.log_up_to(member, season, to=10, on=DAY)
    assert post(member_client, "log", season, n=11, source="currently").status_code == 200
    assert ListEntry.objects.get().progress == 10


def test_undo_takes_back_a_plus_one(member, member_client, season):
    services.log_up_to(member, season, to=2, on=DAY)
    post(member_client, "log", season, n=3, source="currently")
    response = post(member_client, "undo", season, n=3, source="currently")
    assert response.status_code == 200
    assert ListEntry.objects.get().progress == 2
    assert "Next: Episode 3" in body(response)


def test_undo_says_so_only_when_it_undid_something(member_client, season):
    post(member_client, "log", season, n=1)
    assert trigger(post(member_client, "undo", season, n=1))["toast"]["value"] == "Undone"
    assert "toast" not in trigger(post(member_client, "undo", season, n=1))


def test_undo_can_not_touch_another_members_diary(member, other, member_client, season):
    services.log_up_to(other, season, to=3, on=DAY)
    post(member_client, "undo", season, n=3)
    assert ListEntry.objects.get(user=other).progress == 3


# Bulk


def test_bulk_sheet_starts_three_on_and_stops_at_the_end(member, member_client, season):
    services.log_up_to(member, season, to=8, on=DAY)
    html = body(member_client.get(url("bulk", season)))
    assert "data-sheet" in html
    assert 'name="to"' in html
    assert 'value="10"' in html  # three on would pass the end of the season
    assert 'max="10"' in html
    assert 'min="9"' in html
    assert "Watched up to episode" in html
    assert "Give them all the same score" in html


def test_bulk_sheet_for_manga_asks_volumes_not_scores(member_client, manga):
    html = body(member_client.get(url("bulk", manga)))
    assert "Read up to chapter" in html
    assert 'name="volumes"' in html
    assert "Give them all the same score" not in html


def test_bulk_saves_a_range_and_a_score(member, member_client, season):
    services.log_up_to(member, season, to=2, on=DAY)
    response = post(member_client, "bulk", season, to=5, score=7, source="currently")
    assert response.status_code == 200
    entry = ListEntry.objects.get()
    assert (entry.progress, entry.score) == (5, 7)
    assert "sheet-close" in trigger(response)


def test_bulk_sent_twice_is_not_an_error(member_client, season):
    # A navigation mid-send leaves the write queued, and it goes again on the next page.
    post(member_client, "bulk", season, to=5, first=1)
    response = post(member_client, "bulk", season, to=5, first=1)
    assert response.status_code == 200
    assert "toast" not in trigger(response)
    assert ListEntry.objects.get().progress == 5


def test_bulk_to_the_end_raises_the_prompt(member_client, season):
    html = body(post(member_client, "bulk", season, to=10, source="currently"))
    assert "You finished" in html


@pytest.mark.parametrize("to", ["11", "0", "x", ""])
def test_bulk_with_a_bad_number_says_why_and_saves_nothing(member_client, season, to):
    response = post(member_client, "bulk", season, to=to, source="currently")
    assert response.status_code == 400
    assert body(response).strip()
    assert not DiaryEntry.objects.exists()


# Rating


def test_rate_sheet_is_a_real_radio_group_of_half_stars(member_client, movie):
    html = body(member_client.get(url("rate", movie)))
    assert "data-sheet" in html
    assert 'role="radiogroup"' in html or "<fieldset" in html
    # Ten half stars, plus a way to say no rating, all native radios for keyboard and readers.
    assert len(re.findall(r'<input[^>]*type="radio"[^>]*name="score"', html)) == 11
    for half in ("0.5 stars", "1 star", "2.5 stars", "5 stars"):
        assert half in html
    assert "Your rating" in html
    assert ">Save<" in html
    assert "Skip" in html


def test_rate_sheet_shows_the_current_score_checked(member, member_client, movie):
    services.add_diary_row(member, movie, watched_on=DAY, score=7)
    html = body(member_client.get(url("rate", movie)))
    assert re.search(r'<input[^>]*value="7"[^>]*checked', html)


def test_rate_saves_and_clears(member_client, movie):
    post(member_client, "rate", movie, score=6)
    assert ListEntry.objects.get().score == 6
    post(member_client, "rate", movie, score="")
    assert ListEntry.objects.get().score is None


@pytest.mark.parametrize("score", ["0", "11", "x"])
def test_rate_refuses_bad_scores(member_client, movie, score):
    assert post(member_client, "rate", movie, score=score).status_code == 400
    assert not ListEntry.objects.exists()


# Hold, drop, resume


@pytest.mark.parametrize(
    ("status", "heading"),
    [("on_hold", "You put Severance, Season 1 on hold"), ("dropped", "You dropped Severance")],
)
def test_hold_and_drop_leave_currently_and_raise_the_prompt_with_undo(
    member, member_client, season, status, heading
):
    services.log_up_to(member, season, to=3, on=DAY)
    html = body(post(member_client, "status", season, status=status, source="currently"))
    assert ListEntry.objects.get().status == status
    assert heading in html
    assert 'hx-swap-oob="delete"' in html
    assert "Undo" in html
    assert member_client.get("/currently/").content.decode().count('class="current"') == 0


def test_undoing_a_hold_brings_it_back(member, member_client, season):
    services.log_up_to(member, season, to=3, on=DAY)
    post(member_client, "status", season, status="on_hold", source="currently")
    post(member_client, "status", season, status="", source="currently")
    assert ListEntry.objects.get().status == Status.IN_PROGRESS
    assert 'class="current"' in member_client.get("/currently/").content.decode()


def test_status_refuses_anything_else(member_client, season):
    assert post(member_client, "status", season, status="completed").status_code == 400
    assert not ListEntry.objects.exists()


# Currently


def test_the_write_queue_knows_who_it_belongs_to(member, member_client):
    # app.js keeps one queue per member and runs nothing signed out. Both hang off this.
    assert f'data-user="{member.pk}"' in member_client.get("/").content.decode()
    assert 'data-user=""' in Client().get("/login/").content.decode()


def test_currently_matches_the_prototype(member, member_client, season, manga):
    services.log_up_to(member, season, to=9 - 0, on=DAY)
    services.log_up_to(member, manga, to=120, on=DAY)
    html = member_client.get("/currently/").content.decode()
    assert "Severance, Season 1" in html
    assert "Next: Episode 10" in html
    assert "9 / 10" in html
    assert "Next: Chapter 121" in html
    assert "120 / ?" in html
    assert 'aria-label="Log episode 10 of Severance, Season 1"' in html
    assert "+1" in html
    assert "Log several" in html
    assert "Put on hold" in html
    assert ">Drop<" in html
    assert ">Rate<" in html
    assert 'class="empty"' not in html


def test_progress_bar_width_follows_progress(member, member_client, season):
    services.log_up_to(member, season, to=5, on=DAY)
    assert "width: 50%" in member_client.get("/currently/").content.decode()


def test_currently_only_lists_what_is_in_progress(member, member_client, make_season, movie):
    going = make_season(title="Going")
    held = make_season(title="Held")
    done = make_season(title="Done")
    planned = make_season(title="Planned")
    services.log_unit(member, going, on=DAY)
    services.log_unit(member, held, on=DAY)
    services.set_status(member, held, Status.ON_HOLD, on=DAY)
    services.log_up_to(member, done, to=10, on=DAY)
    services.set_watchlist(member, planned, True)
    services.log_unit(member, movie, on=DAY)
    html = member_client.get("/currently/").content.decode()
    assert "Going" in html
    for absent in ("Held", "Done", "Planned", "Oppenheimer"):
        assert absent not in html


def test_currently_is_per_member(member, other, member_client, season):
    services.log_unit(other, season, on=DAY)
    html = member_client.get("/currently/").content.decode()
    assert "Severance" not in html
    assert 'class="empty"' in html


def test_currently_hides_titles_the_member_has_opted_out_of(member, member_client):
    grown = Media.objects.create(
        type="anime", title="Grown", is_adult=True, total_units=3, metadata_source="mal"
    )
    services.log_unit(member, grown, on=DAY)
    assert "Grown" not in member_client.get("/currently/").content.decode()


def test_titles_are_escaped_everywhere(member, member_client, make_season):
    nasty = make_season(title="<script>alert(1)</script>")
    services.log_unit(member, nasty, on=DAY)
    for path in ("/currently/", url("bulk", nasty), url("rate", nasty)):
        assert "<script>alert(1)" not in member_client.get(path).content.decode()
    assert "<script>alert(1)" not in body(post(member_client, "log", nasty, n=2))


# Quick log


def test_quick_log_lists_currently_with_plus_one(member, member_client, season):
    services.log_up_to(member, season, to=2, on=DAY)
    html = member_client.get(reverse("core:quick_log")).content.decode()
    assert "Quick log" in html
    assert "Severance, Season 1" in html
    assert "Next: Episode 3" in html
    assert "+1" in html
    assert "Log something else" in html


def test_quick_log_search_finds_local_titles_only(member_client, movie, upstream_guard):
    url_ = reverse("core:quick_search")
    html = member_client.get(url_, {"q": "oppen"}, headers={"HX-Request": "true"}).content.decode()
    assert "Oppenheimer" in html
    assert reverse("catalogue:title", args=[movie.pk]) in html
    assert "Search everywhere" in html


def test_quick_log_search_with_nothing_typed_is_empty(member_client):
    response = member_client.get(reverse("core:quick_search"), {"q": ""})
    assert response.content == b""


# Title page action button


def actions(client, media):
    return client.get(reverse("catalogue:title", args=[media.pk])).content.decode()


def test_movie_title_says_log_movie_then_log_again(member, member_client, movie):
    html = actions(member_client, movie)
    assert "Log movie" in html
    assert "Add to Watchlist" in html
    services.log_unit(member, movie, on=DAY)
    html = actions(member_client, movie)
    assert "Log again" in html
    assert ">Rate<" in html
    assert "Add to Watchlist" not in html


def test_series_title_says_log_first_then_go_to_currently(member, member_client, season, manga):
    assert "Log episode 1" in actions(member_client, season)
    assert "Log chapter 1" in actions(member_client, manga)
    services.log_unit(member, season, on=DAY)
    html = actions(member_client, season)
    assert "Go to Currently" in html
    assert reverse("core:currently") in html
    assert ">Rate<" in html


def test_title_offers_next_episode_when_on_hold_and_a_rewatch_when_done(
    member, member_client, season
):
    services.log_up_to(member, season, to=3, on=DAY)
    services.set_status(member, season, Status.ON_HOLD, on=DAY)
    html = actions(member_client, season)
    assert "Log episode 4" in html
    assert "On hold" in html
    services.log_up_to(member, season, to=10, on=DAY)
    assert "Log a rewatch" in actions(member_client, season)


def test_watchlist_button_toggles(member_client, movie):
    html = body(post(member_client, "watchlist", movie, on="1", source="title"))
    assert ListEntry.objects.get().status == Status.PLANNED
    assert "Remove from Watchlist" in html
    assert "Remove from Watchlist" in actions(member_client, movie)
    post(member_client, "watchlist", movie, on="0", source="title")
    assert not ListEntry.objects.exists()


def test_watchlist_says_nothing_when_nothing_changed(member, member_client, movie):
    services.log_unit(member, movie, on=DAY)
    response = post(member_client, "watchlist", movie, on="1")
    assert "toast" not in trigger(response)
    assert ListEntry.objects.get().status == Status.COMPLETED


def test_the_title_page_poll_keeps_the_actions(member_client, movie):
    html = member_client.get(reverse("catalogue:title_details", args=[movie.pk])).content.decode()
    assert "Log movie" in html


def test_show_page_offers_the_next_season(member, member_client, show, make_season):
    first = make_season(title="The Bear, Season 1", show=show, season_number=1)
    second = make_season(title="The Bear, Season 2", show=show, season_number=2)
    extras = make_season(title="The Bear, Specials", show=show, season_number=0)
    page = reverse("catalogue:show", args=[show.pk])

    html = member_client.get(page).content.decode()
    assert "Log episode 1 of Season 1" in html
    assert url("log", first) in html

    services.log_up_to(member, first, to=10, on=DAY)
    html = member_client.get(page).content.decode()
    assert "Log episode 1 of Season 2" in html
    assert url("log", second) in html
    assert url("log", extras) not in html

    services.log_unit(member, second, on=DAY)
    assert "Go to Currently" in member_client.get(page).content.decode()

    # Specials are not a next season, even with every numbered one finished.
    services.log_up_to(member, second, to=10, on=DAY)
    html = member_client.get(page).content.decode()
    assert url("log", extras) not in html
    assert "Log episode" not in html


def test_season_rows_on_a_show_page_show_the_members_progress(
    member, member_client, show, make_season
):
    first = make_season(title="The Bear, Season 1", show=show, season_number=1)
    services.log_up_to(member, first, to=4, on=DAY)
    html = member_client.get(reverse("catalogue:show", args=[show.pk])).content.decode()
    assert "4 / 10" in html


# The diary on the title page


def test_title_page_lists_the_members_own_log_rows(member, other, member_client, season):
    services.log_up_to(member, season, to=3, on=date(2026, 10, 3))
    services.log_up_to(other, season, to=7, on=date(2026, 9, 9))
    html = actions(member_client, season)
    assert "Your log" in html
    assert "Episodes 1 to 3" in html
    assert "3 Oct 2026" in html
    assert "9 Sep" not in html


def test_edit_sheet_edits_a_row(member, member_client, season):
    services.log_up_to(member, season, to=3, on=DAY)
    row = DiaryEntry.objects.get()
    edit = reverse("tracking:diary_edit", args=[row.pk])
    html = member_client.get(edit).content.decode()
    assert 'name="watched_on"' in html
    assert 'name="episode_from"' in html
    assert 'name="episode_to"' in html
    assert 'value="2026-10-24"' in html
    response = member_client.post(
        edit,
        {"watched_on": "2026-10-20", "episode_from": 1, "episode_to": 5, "score": 8},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    entry = ListEntry.objects.get()
    assert (entry.progress, entry.score, entry.started_on) == (5, 8, date(2026, 10, 20))


def test_edit_with_a_bad_range_says_what_is_wrong_and_keeps_the_typing(
    member, member_client, season
):
    services.log_up_to(member, season, to=3, on=DAY)
    row = DiaryEntry.objects.get()
    response = member_client.post(
        reverse("tracking:diary_edit", args=[row.pk]),
        {"watched_on": "2026-10-20", "episode_from": 9, "episode_to": 5},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 400
    html = response.content.decode()
    assert "first episode" in html.lower()
    assert 'value="9"' in html
    row.refresh_from_db()
    assert row.episode_to == 3


def test_a_date_can_be_blank_on_edit(member, member_client, movie):
    services.log_unit(member, movie, on=DAY)
    row = DiaryEntry.objects.get()
    member_client.post(reverse("tracking:diary_edit", args=[row.pk]), {"watched_on": ""})
    row.refresh_from_db()
    assert row.watched_on is None


def test_delete_needs_post_and_confirms_on_the_client(member, member_client, season):
    services.log_up_to(member, season, to=3, on=DAY)
    row = DiaryEntry.objects.get()
    delete = reverse("tracking:diary_delete", args=[row.pk])
    assert member_client.get(delete).status_code == 405
    html = member_client.get(reverse("tracking:diary_edit", args=[row.pk])).content.decode()
    assert "data-confirm" in html
    assert "btn--danger" in html
    assert member_client.post(delete, headers={"HX-Request": "true"}).status_code == 200
    assert not DiaryEntry.objects.exists()


def test_nobody_edits_or_deletes_another_members_row(member, other, member_client, season):
    services.log_up_to(other, season, to=3, on=DAY)
    row = DiaryEntry.objects.get()
    assert member_client.get(reverse("tracking:diary_edit", args=[row.pk])).status_code == 404
    assert (
        member_client.post(
            reverse("tracking:diary_edit", args=[row.pk]), {"episode_from": 1, "episode_to": 9}
        ).status_code
        == 404
    )
    assert member_client.post(reverse("tracking:diary_delete", args=[row.pk])).status_code == 404
    row.refresh_from_db()
    assert row.episode_to == 3


# Library


def library(client, **params):
    return client.get("/library/", params).content.decode()


@pytest.fixture
def stocked(member, make_movie, make_season, manga, show):
    dune = make_movie("Dune: Part Two")
    oldboy = make_movie("Oldboy")
    first = make_season(title="The Bear, Season 1", show=show, season_number=1)
    second = make_season(title="The Bear, Season 2", show=show, season_number=2)
    services.log_unit(member, dune, on=date(2026, 10, 24))
    services.rate(member, dune, 9)
    services.rate(member, oldboy, 10)  # undated
    services.log_up_to(member, first, to=10, score=8, on=date(2026, 8, 2))
    services.log_up_to(member, second, to=4, score=4, on=date(2026, 8, 10))
    services.set_status(member, second, Status.DROPPED, on=date(2026, 8, 19))
    services.log_up_to(member, manga, to=20, on=date(2026, 9, 18))
    services.set_status(member, manga, Status.ON_HOLD, on=date(2026, 9, 18))
    return dune


def test_library_groups_by_month_with_day_status_and_stars(member_client, stocked):
    html = library(member_client)
    assert "October 2026" in html
    assert "September 2026" in html
    assert "August 2026" in html
    assert "No date" in html
    assert html.index("October 2026") < html.index("September 2026") < html.index("No date")
    assert "Logged" in html  # a movie is Logged, not Completed
    assert "On hold" in html
    assert "Dropped" in html
    assert "★★★★½" in html
    assert ">24<" in html
    assert "Unrated" in html


def test_library_rolls_seasons_up_under_their_show(member_client, stocked):
    html = library(member_client)
    assert html.count("The Bear") >= 1
    assert "Season 1" in html
    assert "Season 2" in html
    assert 'aria-label="Show seasons of The Bear"' in html
    assert 'aria-expanded="false"' in html
    # Show score is floor(mean of rated seasons): (8 + 4) / 2 = 6, three stars.
    show_row = html[html.index('data-row="The Bear"') :]
    assert "★★★" in show_row[: show_row.index("Season 1")]
    # A show takes the status and date of its latest season.
    assert "Dropped" in show_row[: show_row.index("Season 1")]


def test_library_leaves_specials_out_of_the_show_score(member, member_client, show, make_season):
    first = make_season(title="The Bear, Season 1", show=show, season_number=1)
    extras = make_season(title="The Bear, Specials", show=show, season_number=0, total=1)
    services.log_up_to(member, first, to=10, score=8, on=DAY)
    services.log_up_to(member, extras, to=1, score=2, on=DAY)
    html = library(member_client)
    show_row = html[html.index('data-row="The Bear"') :]
    assert "★★★★" in show_row[: show_row.index("Season 1")]


def test_library_status_filter(member_client, stocked):
    html = library(member_client, status="on_hold")
    assert "Berserk" in html
    assert "Dune" not in html
    assert "The Bear" not in html
    html = library(member_client, status="dropped")
    assert "The Bear" in html
    html = library(member_client, status="completed")
    assert "Dune" in html
    assert "The Bear" in html  # one of its seasons is
    assert "Berserk" not in html


def test_library_type_filter_is_multi_select(member_client, stocked):
    html = library(member_client, types="movie")
    assert "Dune" in html
    assert "Berserk" not in html
    html = library(member_client, types="movie,manga")
    assert "Dune" in html
    assert "Berserk" in html
    assert "The Bear" not in html
    assert 'aria-pressed="true"' in html
    assert 'aria-pressed="false"' in html


def test_library_with_every_type_off_says_nothing_matches(member_client, stocked):
    html = library(member_client, types="none")
    assert "No titles match these filters." in html


def test_library_sort_by_score_has_no_month_headings(member_client, stocked):
    html = library(member_client, sort="score")
    assert "By score" in html
    assert "October 2026" not in html
    assert html.index("Oldboy") < html.index("Dune") < html.index("Berserk")


def test_library_leaves_out_what_is_in_progress_or_planned(
    member, member_client, season, make_season
):
    services.log_unit(member, season, on=DAY)
    services.set_watchlist(member, make_season(title="Andor"), True)
    html = library(member_client)
    assert "Severance" not in html
    assert "Andor" not in html


def test_empty_library_has_a_designed_empty_state(member_client):
    html = library(member_client)
    assert 'class="empty"' in html


def test_library_is_per_member(other, member_client, movie):
    services.log_unit(other, movie, on=DAY)
    assert "Oppenheimer" not in library(member_client)


def test_library_filters_answer_htmx_with_only_the_list(member_client, stocked):
    response = member_client.get("/library/", {"status": "on_hold"}, headers={"HX-Request": "true"})
    html = body(response)
    assert "<html" not in html
    assert "Berserk" in html
    assert "HX-Request" in response.headers.get("Vary", "")


def test_a_history_restore_gets_the_whole_page_not_the_fragment(member_client, stocked):
    # htmx sends both headers when it has lost its copy of a page someone stepped back to.
    response = member_client.get(
        "/library/",
        {"status": "on_hold"},
        headers={"HX-Request": "true", "HX-History-Restore-Request": "true"},
    )
    assert "<html" in body(response)


def test_a_long_library_comes_a_page_at_a_time(member, member_client, make_movie):
    for index in range(70):
        services.log_unit(member, make_movie(f"Film {index:02}"), on=DAY)
    html = library(member_client)
    assert html.count("data-row=") == 50
    assert 'hx-trigger="revealed"' in html
    more = member_client.get("/library/", {"page": 2}, headers={"HX-Request": "true"})
    assert body(more).count("data-row=") == 20
    assert 'hx-trigger="revealed"' not in body(more)
    # The month heading is not repeated where the second page joins on.
    assert "October 2026" not in body(more)


def test_library_query_count_does_not_grow_with_rows(
    member, member_client, make_movie, django_assert_max_num_queries
):
    for index in range(30):
        services.log_unit(member, make_movie(f"Film {index:02}"), on=DAY)
    with django_assert_max_num_queries(12):
        member_client.get("/library/")


# Stats and favourites on the profile


def test_profile_shows_stats_and_the_library_link(member, member_client, movie, make_movie):
    past = make_movie("Past Lives")
    services.set_watchlist(member, past, True)
    services.log_unit(member, movie, on=DAY)
    html = member_client.get("/me/").content.decode()
    assert "Stats" in html and "Favourites" in html
    assert "Movies" in html and "Episodes" in html
    assert reverse("social:profile_library", args=[member.username]) in html
    assert "Past Lives" not in html


def test_favourites_tab_shows_the_best_rated(member, member_client, movie):
    services.add_diary_row(member, movie, watched_on=DAY, score=9)
    html = member_client.get("/me/").content.decode()
    assert reverse("catalogue:title", args=[movie.pk]) in html
    assert "9.0" in html


def test_empty_favourites_says_how_to_fill(member_client):
    html = member_client.get("/me/").content.decode()
    assert "Rate things to fill this in." in html


# Home


def home(client):
    return client.get("/").content.decode()


def test_home_continue_is_what_this_member_has_going(member, other, member_client, season, anime):
    services.log_unit(member, season, on=DAY)
    services.log_unit(other, anime, on=DAY)
    html = home(member_client)
    assert "Continue" in html
    continuing = html[html.index("Continue") :]
    continuing = continuing[: continuing.index("</section>")]
    assert reverse("catalogue:title", args=[season.pk]) in continuing
    assert reverse("catalogue:title", args=[anime.pk]) not in continuing


def test_home_hides_continue_when_nothing_is_going(member_client, movie):
    assert "Continue" not in home(member_client)


def test_home_recently_added_is_the_circle_not_me_and_not_private(
    member, other, member_client, make_movie
):
    mine = make_movie("Mine")
    theirs = make_movie("Theirs")
    hidden = make_movie("Hidden")
    planned = make_movie("Only planned")
    services.log_unit(member, mine, on=DAY)
    services.log_unit(other, theirs, on=DAY)
    services.log_unit(other, hidden, on=DAY)
    services.set_user_fields(other, hidden, visibility="private")
    services.set_watchlist(other, planned, True)
    html = home(member_client)
    section = html[html.index("Recently added") :]
    section = section[: section.index("</section>")]
    assert reverse("catalogue:title", args=[theirs.pk]) in section
    assert reverse("catalogue:title", args=[mine.pk]) not in section
    assert reverse("catalogue:title", args=[hidden.pk]) not in section
    assert reverse("catalogue:title", args=[planned.pk]) not in section


def test_home_popular_ranks_by_how_many_members_have_it(member, other, member_client, make_movie):
    make_movie("Newest but nobody has it")
    loved = make_movie("Loved")
    services.log_unit(member, loved, on=DAY)
    services.log_unit(other, loved, on=DAY)
    html = home(member_client)
    section = html[html.index("Popular movies") :]
    assert section.index("Loved") < section.index("Newest but nobody")


def test_home_popular_does_not_count_private_entries(member, other, member_client, make_movie):
    public = make_movie("Public")
    hush = make_movie("Hush")
    services.log_unit(other, public, on=DAY)
    for user in (member, other):
        services.log_unit(user, hush, on=DAY)
        services.set_user_fields(user, hush, visibility="private")
    html = home(member_client)
    section = html[html.index("Popular movies") :]
    assert section.index("Public") < section.index("Hush")


def test_home_popular_tv_counts_members_of_any_season(member, other, member_client, make_season):
    quiet = Show.objects.create(title="Quiet", metadata_source="tmdb")
    loud = Show.objects.create(title="Loud", metadata_source="tmdb")
    make_season(title="Quiet, Season 1", show=quiet, season_number=1)
    season = make_season(title="Loud, Season 1", show=loud, season_number=1)
    services.log_unit(member, season, on=DAY)
    services.log_unit(other, season, on=DAY)
    html = home(member_client)
    section = html[html.index("Popular TV") :]
    first_link = re.search(r'href="(/show/\d+/)"', section).group(1)
    assert first_link == reverse("catalogue:show", args=[loud.pk])


def test_home_never_calls_upstream(member, member_client, movie, upstream_guard):
    services.log_unit(member, movie, on=DAY)
    member_client.get("/")
    assert upstream_guard.calls == []


def test_home_query_count_does_not_grow_with_titles(
    member, member_client, make_movie, django_assert_max_num_queries
):
    for index in range(12):
        services.log_unit(member, make_movie(f"Film {index:02}"), on=DAY)
    with django_assert_max_num_queries(12):
        member_client.get("/")


# Demo data


def test_seed_demo_can_fill_one_members_library_for_screenshots(member, settings):
    from django.core.management import call_command

    settings.DEBUG = True
    call_command("seed_demo", "--library-for", member.username, verbosity=0)
    assert ListEntry.objects.filter(user=member, status=Status.IN_PROGRESS).exists()
    assert ListEntry.objects.filter(user=member, status=Status.COMPLETED).exists()
    assert ListEntry.objects.filter(user=member, status=Status.PLANNED).exists()
    assert services.rebuild_entries() == 0
    call_command("seed_demo", "--remove", verbosity=0)
    assert not ListEntry.objects.filter(media__metadata_source="demo").exists()


def test_a_row_coming_back_is_whole_not_a_scatter_of_fragments(member, member_client, season):
    # The list comes back as one out-of-band swap. Anything out-of-band nested inside it gets
    # pulled out and thrown away by the page, leaving a row with no progress or +1.
    services.log_up_to(member, season, to=3, on=DAY)
    post(member_client, "status", season, status="on_hold")
    html = body(post(member_client, "status", season, status=""))
    listed = html[html.index('id="currently-list"') :]
    assert f'id="entry-{season.pk}-info"' in listed
    assert "hx-swap-oob" not in listed.split(">", 1)[1].split('id="title-actions')[0]
