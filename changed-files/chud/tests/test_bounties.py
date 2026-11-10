"""A bounty: points leave now, the title joins the friend's Watchlist, and they collect by
finishing it. A rating of four stars or more pays the setter a bonus of new points."""

from datetime import timedelta

import pytest
from django.utils import timezone

from chud import selectors, services
from chud.models import Bounty, ChudLedger
from tracking import services as tracking
from tracking.models import DiaryEntry, ListEntry, Status

from .conftest import DAY, balance

pytestmark = pytest.mark.django_db


@pytest.fixture
def funded(member, give):
    give(member, points=500)
    return member


def points_without_watching(user):
    earned = ChudLedger.objects.filter(user=user, kind__in=("earn", "unearn"))
    return selectors.account(user).points - sum(r.points for r in earned)


def test_setting_one_takes_the_points_and_adds_it_to_their_watchlist(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    assert balance(funded)[0] == 300
    assert bounty.status == Bounty.Status.OPEN
    assert ListEntry.objects.get(user=other, media=season).user_status == Status.PLANNED
    row = ChudLedger.objects.filter(user=funded).latest("pk")
    assert (row.kind, row.points) == (ChudLedger.Kind.BOUNTY_SET, -200)
    assert row.text == "Bounty on Severance, Season 1 for Kev"
    assert row.counterparty == other and row.media == season and row.bounty == bounty


def test_it_leaves_a_title_they_have_started_alone(funded, other, season):
    tracking.log_up_to(other, season, 2, on=DAY)
    services.place_bounty(funded, other, season, 10)
    assert ListEntry.objects.get(user=other, media=season).status == Status.IN_PROGRESS


@pytest.mark.parametrize("amount", [0, -5])
def test_a_bounty_must_be_some_points(funded, other, season, amount):
    with pytest.raises(services.ChudError):
        services.place_bounty(funded, other, season, amount)
    assert balance(funded)[0] == 500


def test_you_cannot_set_more_than_you_have(funded, other, season):
    with pytest.raises(services.ChudError):
        services.place_bounty(funded, other, season, 501)
    assert balance(funded)[0] == 500
    assert not ListEntry.objects.filter(user=other).exists()


def test_not_on_yourself(funded, season):
    with pytest.raises(services.ChudError, match="yourself"):
        services.place_bounty(funded, funded, season, 10)


def test_not_on_someone_private_or_deactivated(funded, other, season):
    other.default_visibility = "private"
    other.save()
    with pytest.raises(services.ChudError):
        services.place_bounty(funded, other, season, 10)
    other.default_visibility = "members"
    other.is_active = False
    other.save()
    with pytest.raises(services.ChudError):
        services.place_bounty(funded, other, season, 10)
    assert balance(funded)[0] == 500


def test_not_on_something_they_have_finished(funded, other, season):
    tracking.log_up_to(other, season, 10, on=DAY)
    with pytest.raises(services.ChudError, match="already finished"):
        services.place_bounty(funded, other, season, 10)


def test_not_on_an_adult_title_they_have_not_asked_for(funded, other, make_movie):
    adult = make_movie(title="Adult", is_adult=True)
    with pytest.raises(services.ChudError):
        services.place_bounty(funded, other, adult, 10)


def test_one_open_bounty_per_person_title_and_friend(funded, other, season):
    services.place_bounty(funded, other, season, 10)
    with pytest.raises(services.ChudError, match="already"):
        services.place_bounty(funded, other, season, 10)
    assert balance(funded)[0] == 490


def test_two_friends_can_each_set_one(funded, other, third, give, season):
    give(third, points=50)
    services.place_bounty(funded, other, season, 10)
    services.place_bounty(third, other, season, 20)
    assert Bounty.objects.filter(recipient=other, status="open").count() == 2


def test_the_same_token_is_one_bounty(funded, other, season):
    first = services.place_bounty(funded, other, season, 10, token="t")
    second = services.place_bounty(funded, other, season, 10, token="t")
    assert first == second
    assert balance(funded)[0] == 490


# Collecting


def test_finishing_collects_the_whole_bounty_as_points_only(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    tracking.log_up_to(other, season, 10, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED
    assert points_without_watching(other) == 200
    row = ChudLedger.objects.filter(user=other, kind="bounty_collect").get()
    assert (row.points, row.xp) == (200, 0)
    assert row.text == "Maya's bounty on Severance, Season 1"
    assert balance(funded)[0] == 300


def test_a_movie_collects_when_it_is_logged(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 50)
    tracking.log_unit(other, movie, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED


def test_part_of_it_collects_nothing(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    tracking.log_up_to(other, season, 9, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.OPEN


@pytest.mark.parametrize("status", ["dropped", "on_hold"])
def test_dropping_or_holding_collects_nothing(funded, other, season, status):
    bounty = services.place_bounty(funded, other, season, 200)
    tracking.log_up_to(other, season, 3, on=DAY)
    tracking.set_status(other, season, status, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.OPEN
    assert points_without_watching(other) == 0


def test_an_import_collects_nothing(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    tracking.add_diary_row(
        other, season, episode_from=1, episode_to=10, source=DiaryEntry.Source.MAL
    )
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.OPEN
    assert balance(other) == (0, 0)


def test_finishing_by_hand_after_a_part_import_collects(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    tracking.add_diary_row(
        other, season, episode_from=1, episode_to=9, source=DiaryEntry.Source.MAL
    )
    tracking.log_unit(other, season, n=10, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED


def test_a_season_that_finishes_airing_under_them_collects(funded, other, make_season):
    airing = make_season(title="Airing", total=2, status="releasing", runtime_min=30)
    bounty = services.place_bounty(funded, other, airing, 50)
    tracking.log_up_to(other, airing, 2, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.OPEN
    airing.airing_status = "finished"
    airing.save()
    tracking.recompute_media(airing)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED


def test_two_bounties_on_one_title_both_collect(funded, other, third, give, season):
    give(third, points=50)
    services.place_bounty(funded, other, season, 10)
    services.place_bounty(third, other, season, 20)
    tracking.log_up_to(other, season, 10, on=DAY)
    assert points_without_watching(other) == 30


def test_it_collects_once(funded, other, movie):
    services.place_bounty(funded, other, movie, 50)
    tracking.log_unit(other, movie, on=DAY)
    tracking.log_unit(other, movie, on=DAY + timedelta(days=1))
    tracking.rebuild_entries()
    assert points_without_watching(other) == 50


# Cancelling


def test_cancelling_refunds_in_full(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    services.cancel_bounty(bounty, funded)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.CANCELLED
    assert balance(funded)[0] == 500
    row = ChudLedger.objects.filter(user=funded).latest("pk")
    assert (row.kind, row.points) == (ChudLedger.Kind.BOUNTY_REFUND, 200)


def test_cancelling_twice_refunds_once(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    services.cancel_bounty(bounty, funded)
    services.cancel_bounty(bounty, funded)
    assert balance(funded)[0] == 500


def test_only_the_setter_can_cancel(funded, other, season):
    bounty = services.place_bounty(funded, other, season, 200)
    with pytest.raises(services.ChudError):
        services.cancel_bounty(bounty, other)
    assert balance(funded)[0] == 300


def test_a_collected_bounty_cannot_be_cancelled(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 50)
    tracking.log_unit(other, movie, on=DAY)
    with pytest.raises(services.ChudError, match="collected"):
        services.cancel_bounty(bounty, funded)
    assert balance(funded)[0] == 450


def test_a_cancelled_bounty_can_be_set_again_and_collects_nothing(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 50)
    services.cancel_bounty(bounty, funded)
    tracking.log_unit(other, movie, on=DAY)
    assert points_without_watching(other) == 0


# The taste bonus


def test_rating_four_stars_on_finishing_pays_the_setter_a_fifth_as_new_points(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 100)
    tracking.log_unit(other, movie, on=DAY)
    assert points_without_watching(funded) == 500 - 100
    tracking.rate(other, movie, 8, on=DAY)
    assert balance(funded)[0] == 400 + 20
    assert points_without_watching(other) == 100
    bounty.refresh_from_db()
    assert bounty.bonus_paid
    row = ChudLedger.objects.filter(user=funded, kind="bounty_bonus").get()
    assert row.text == "Kev rated Oppenheimer 4 stars or higher"
    assert (row.points, row.xp) == (20, 0)


def test_rated_before_finishing_counts_too(funded, other, make_season):
    short = make_season(title="Short", total=2, runtime_min=20)
    services.place_bounty(funded, other, short, 100)
    tracking.log_unit(other, short, n=1, on=DAY)
    tracking.rate(other, short, 9, on=DAY)
    assert balance(funded)[0] == 400
    tracking.log_unit(other, short, n=2, on=DAY)
    assert balance(funded)[0] == 420


def test_under_four_stars_pays_no_bonus(funded, other, movie):
    services.place_bounty(funded, other, movie, 100)
    tracking.log_unit(other, movie, on=DAY)
    tracking.rate(other, movie, 7, on=DAY)
    assert balance(funded)[0] == 400


def test_the_bonus_pays_once_however_often_they_rate(funded, other, movie):
    services.place_bounty(funded, other, movie, 100)
    tracking.log_unit(other, movie, on=DAY)
    tracking.rate(other, movie, 8, on=DAY)
    tracking.rate(other, movie, 6, on=DAY)
    tracking.rate(other, movie, 10, on=DAY)
    assert balance(funded)[0] == 420


def test_the_bonus_rounds_and_a_tiny_one_is_nothing(funded, other, movie, make_movie):
    services.place_bounty(funded, other, movie, 13)
    tracking.log_unit(other, movie, on=DAY)
    tracking.rate(other, movie, 8, on=DAY)
    assert balance(funded)[0] == 500 - 13 + 3
    tiny = make_movie(title="Tiny", runtime_min=10)
    services.place_bounty(funded, other, tiny, 2)
    before = balance(funded)[0]
    tracking.log_unit(other, tiny, on=DAY)
    tracking.rate(other, tiny, 10, on=DAY)
    assert balance(funded)[0] == before


# Taking the log back


def test_undoing_the_finish_takes_the_bounty_back_and_reopens_it(funded, other, make_season):
    short = make_season(title="Short", total=2, runtime_min=20)
    bounty = services.place_bounty(funded, other, short, 100)
    tracking.log_up_to(other, short, 2, on=DAY)
    tracking.rate(other, short, 10, on=DAY)
    assert balance(funded)[0] == 420
    tracking.undo_unit(other, short, n=2)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.OPEN
    assert not bounty.bonus_paid
    assert balance(funded)[0] == 400
    assert points_without_watching(other) == 0
    assert services.verify() == []
    tracking.log_unit(other, short, n=2, on=DAY)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED


def test_taking_back_a_bounty_already_spent_goes_negative(funded, other, make_season):
    short = make_season(title="Short", total=2, runtime_min=20)
    services.place_bounty(funded, other, short, 100)
    tracking.log_up_to(other, short, 2, on=DAY)
    points = balance(other)[0]
    services.adjust(other, points=-points, text="Spent it")
    tracking.undo_unit(other, short, n=2)
    assert balance(other)[0] < -90
    assert services.verify() == []


def test_undoing_a_later_rewatch_keeps_the_bounty(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 100)
    tracking.log_unit(other, movie, on=DAY)
    tracking.log_unit(other, movie, on=DAY + timedelta(days=1))
    tracking.undo_unit(other, movie)
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.COLLECTED


# Merging


def test_a_merge_moves_a_bounty_to_the_survivor(funded, other, season, make_season):
    from catalogue.merge import merge_media

    twin = make_season(title="Twin", total=10, runtime_min=50)
    bounty = services.place_bounty(funded, other, twin, 50)
    merge_media(twin, season)
    bounty.refresh_from_db()
    assert bounty.media == season


def test_a_merge_of_two_open_bounties_refunds_the_one_that_goes(funded, other, season, make_season):
    from catalogue.merge import merge_media

    twin = make_season(title="Twin", total=10, runtime_min=50)
    services.place_bounty(funded, other, season, 50)
    services.place_bounty(funded, other, twin, 30)
    merge_media(twin, season)
    assert Bounty.objects.filter(status="open").get().amount == 50
    assert balance(funded)[0] == 450
    assert services.verify() == []


def test_an_expired_bounty_pays_the_sender_back_instead_of_collecting(funded, other, movie):
    bounty = services.place_bounty(funded, other, movie, 40)
    Bounty.objects.filter(pk=bounty.pk).update(expires_at=timezone.now() - timedelta(days=1))
    tracking.add_diary_row(other, movie, watched_on=DAY)
    row = ChudLedger.objects.filter(user=funded, kind=ChudLedger.Kind.BOUNTY_REFUND).latest("pk")
    assert row.points == 40
    bounty.refresh_from_db()
    assert bounty.status == Bounty.Status.CANCELLED
    assert balance(funded)[0] == 500
