"""The rules with no database: levels, the earn sum, the catalogues. Numbers come from running the
prototype's own expressions (ui-logic.js: xpFloor, levelFor, earnPatch)."""

import pytest

from chud import rules


@pytest.mark.parametrize(
    "level,floor",
    [(1, 0), (2, 100), (3, 300), (5, 1000), (10, 4500), (15, 10500), (20, 19000), (142, 1001100)],
)
def test_the_xp_floor_is_50_l_l_minus_1(level, floor):
    assert rules.xp_floor(level) == floor


@pytest.mark.parametrize(
    "xp,level",
    [
        (0, 1),
        (99, 1),
        (100, 2),
        (299, 2),
        (300, 3),
        (999, 4),
        (1000, 5),
        (4460, 9),
        (4500, 10),
        (1_000_000, 141),
    ],
)
def test_the_level_is_the_highest_floor_reached(xp, level):
    assert rules.level_for(xp) == level


@pytest.mark.parametrize(
    "hours,run_hours,active,expected",
    [
        # A two hour movie: the prototype's own "Finished Dune: Part Two" +27.
        (2, 2, 1, 27),
        # Six hours a day is the full 2x.
        (6, 6, 1, 120),
        (1, 60, 1, 20),
        # A slow run is close to 1x.
        (50 / 60, 500 / 60, 10, 9),
        # Never nothing.
        (0.001, 0.001, 1, 1),
    ],
)
def test_the_amount_is_hours_times_ten_times_the_pace(hours, run_hours, active, expected):
    assert rules.earned(hours, run_hours, active) == expected


def test_a_day_on_hold_is_not_an_active_day_and_there_is_always_one():
    assert rules.earned(1, 12, 2) == rules.earned(1, 6, 1)
    assert rules.earned(1, 6, 0) == rules.earned(1, 6, 1)


def test_one_log_can_only_earn_so_much():
    assert rules.MAX_AWARD_HOURS == 24
    assert rules.capped_hours(10) == 10
    assert rules.capped_hours(400) == 24


@pytest.mark.parametrize(
    "sticker,name,price,payout",
    [
        ("grass", "Touch Grass", 50, 35),
        ("cooked", "Cooked", 100, 70),
        ("sleep", "No Sleep", 150, 105),
        ("peak", "Peak", 250, 175),
        ("cinema", "Absolute Cinema", 500, 350),
    ],
)
def test_the_sticker_catalogue(sticker, name, price, payout):
    found = rules.sticker(sticker)
    assert (found.name, found.price, found.payout) == (name, price, payout)
    assert found.bg.startswith("#") and found.fg.startswith("#") and found.d


@pytest.mark.parametrize(
    "buddy,name,level",
    [
        ("goblin", "Couch Goblin", 5),
        ("gremlin", "Screen Gremlin", 10),
        ("beast", "Binge Beast", 15),
        ("final", "The Final Chud", 20),
    ],
)
def test_the_buddy_catalogue(buddy, name, level):
    found = rules.buddy(buddy)
    assert (found.name, found.level) == (name, level)
    assert found.fill.startswith("#") and found.head and found.face


def test_unknown_ids_are_none():
    assert rules.sticker("nope") is None
    assert rules.buddy("nope") is None


def test_buddies_crossed_lists_only_those_between_two_levels():
    assert [b.id for b in rules.buddies_crossed(4, 5)] == ["goblin"]
    assert [b.id for b in rules.buddies_crossed(5, 5)] == []
    assert [b.id for b in rules.buddies_crossed(1, 15)] == ["goblin", "gremlin", "beast"]


def test_xp_line_says_the_next_level_and_the_next_buddy():
    assert rules.xp_line(4460) == "4,460 XP. 40 to level 10. New buddy at level 10"
    assert rules.xp_line(19000) == "19,000 XP. 2,000 to level 21. New buddy at level 25"
    assert rules.xp_percent(4460) == 96
    assert rules.xp_percent(0) == 0
