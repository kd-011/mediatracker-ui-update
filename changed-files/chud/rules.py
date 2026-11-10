"""The CHUD rules, with no database: levels, the earn sum, and the sticker and buddy catalogues.
Ported from the prototype (ui-logic.js: stickers, buddies, xpFloor, levelFor, earnPatch)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Sticker:
    id: str
    name: str
    price: int
    bg: str
    fg: str
    d: str

    @property
    def payout(self):
        """What the recipient gets: 70 percent of the price, rounded."""
        return (self.price * 7 + 5) // 10


@dataclass(frozen=True)
class Buddy:
    id: str
    name: str
    level: int
    fill: str
    head: str
    face: str


STICKERS = (
    Sticker(
        "grass",
        "Touch Grass",
        50,
        "#2F6B45",
        "#D9F5DF",
        "M6 20c0-5-1-8-3-10 3 1 5 4 6 7 0-5 1-9 3-13 2 4 3 8 3 13 1-3 3-6 6-7-2 2-3 5-3 10z",
    ),
    Sticker(
        "cooked",
        "Cooked",
        100,
        "#B2401F",
        "#FFE3B0",
        "M12 2c1 4 6 7 6 12a6 6 0 0 1-12 0c0-3 2-5 3-8 1 1 2 2 2 4 1-2 1-5 1-8z",
    ),
    Sticker(
        "sleep",
        "No Sleep",
        150,
        "#2C3A78",
        "#E8E6FF",
        "M20 14.500A9 9 0 1 1 9.500 4a7 7 0 0 0 10.500 10.500z",
    ),
    Sticker(
        "peak",
        "Peak",
        250,
        "#8A5A00",
        "#FFE9A8",
        "M12 2l3 6.500 7 .9-5.200 4.800 1.400 7L12 17.800 5.800 21.200l1.400-7L2 9.400l7-.9z",
    ),
    Sticker(
        "cinema",
        "Absolute Cinema",
        500,
        "#6B1F52",
        "#FFD9EE",
        "M3 19L2 7l6 4 4-7 4 7 6-4-1 12z",
    ),
)

BUDDIES = (
    Buddy(
        "goblin",
        "Couch Goblin",
        5,
        "#7FCF8E",
        "M5 9L1 6l6 .5a8 8 0 0 1 10 0L23 6l-4 3a8 8 0 1 1-14 0z",
        "M9 12h.01M15 12h.01M9 16.500c2 1.300 4 1.300 6 0",
    ),
    Buddy(
        "gremlin",
        "Screen Gremlin",
        10,
        "#7CC7FF",
        "M3 7h18v14H3zM7 7L5 2h2l3 5zM17 7l2-5h-2l-3 5z",
        "M8 12h.01M16 12h.01M8 17h8",
    ),
    Buddy(
        "beast",
        "Binge Beast",
        15,
        "#FF8A7A",
        "M12 1l3 4 5-1-1 5 4 3-4 3 1 5-5-1-3 4-3-4-5 1 1-5-4-3 4-3-1-5 5 1z",
        "M9 11h.01M15 11h.01M8.500 15.500l2 1 1.500-1 1.500 1 2-1",
    ),
    Buddy(
        "final",
        "The Final Chud",
        20,
        "#FFB224",
        "M4 10L3 3l4 3 5-4 5 4 4-3-1 7a8.500 8.500 0 1 1-16 0z",
        "M9 13h.01M15 13h.01M8.500 17c2.300 1.500 4.700 1.500 7 0",
    ),
    Buddy(
        "modem",
        "Modem Moth",
        25,
        "#B39DDB",
        "M12 3l4 3 5-2-1 6 3 4-5 2-6 6-6-6-5-2 3-4-1-6 5 2z",
        "M9 11h.01M15 11h.01M10 15h4",
    ),
    Buddy(
        "rat",
        "Radiator Rat",
        30,
        "#4DD0C4",
        "M4 10a3 3 0 0 1 3-4 8 8 0 0 1 10 0 3 3 0 0 1 3 4 8 8 0 1 1-16 0z",
        "M9 12h.01M15 12h.01M9 16h6M12 13.500v2.500",
    ),
    Buddy(
        "demon",
        "Dial-Up Demon",
        35,
        "#F48FB1",
        "M12 2l2.500 3L18 3l-.500 4L21 9l-3 2 1 4-4 .500L12 21l-2.500-5.500L5 15"
        "l1-4-3-2 3.500-2L6 3l3.500 2z",
        "M9 11h.01M15 11h.01M9 16l2-1 1 1 1-1 2 1",
    ),
)

# A sanity cap, not a daily cap: one log can earn at most a day of watching, which at the full 2x
# is 480 points. Catching up on 1,100 episodes in one tap is an import in all but name.
MAX_AWARD_HOURS = 24

# A bounty sits open for this long, then it is dead: the sender cancels to reclaim, or finishing
# it after expiry pays the sender back instead of the recipient.
BOUNTY_WINDOW_DAYS = 14

SPENDING_BLOCKED = "Spending is blocked until you're back above zero."

# Four stars. Scores are stored from 1 to 10, in half stars.
BONUS_SCORE = 8

_STICKERS = {s.id: s for s in STICKERS}
_BUDDIES = {b.id: b for b in BUDDIES}


def sticker(sticker_id):
    return _STICKERS.get(sticker_id)


def buddy(buddy_id):
    return _BUDDIES.get(buddy_id)


def xp_floor(level):
    return 50 * level * (level - 1)


def level_for(xp):
    level = 1
    while xp >= xp_floor(level + 1):
        level += 1
    return level


def _round(value):
    """Halves go up, as the prototype's Math.round does."""
    return int(value + 0.5)


def capped_hours(hours):
    return min(hours, MAX_AWARD_HOURS)


def earned(hours, run_hours, active_days):
    """Points and XP for `hours` of watching, on a run of `run_hours` over `active_days`. Six hours
    a day is a CHUD score of 100, which doubles it."""
    active = max(1, active_days)
    chud = min(100, (run_hours / active / 6) * 100)
    return max(1, _round(hours * 10 * (1 + chud / 100)))


def taste_bonus(amount):
    """20 percent of a bounty, rounded. New points, not taken from what the friend collects."""
    return (amount * 2 + 5) // 10


def buddies_crossed(before, after):
    return [b for b in BUDDIES if before < b.level <= after]


def next_buddy(level):
    return next((b for b in BUDDIES if b.level > level), None)


def xp_percent(xp):
    level = level_for(xp)
    floor = xp_floor(level)
    return _round((xp - floor) / (xp_floor(level + 1) - floor) * 100)


def xp_line(xp):
    level = level_for(xp)
    to_next = xp_floor(level + 1) - xp
    line = f"{xp:,} XP. {to_next:,} to level {level + 1}"
    upcoming = next_buddy(level)
    return f"{line}. New buddy at level {upcoming.level}" if upcoming else line


def points_short(short):
    return f"{short} more point{'' if short == 1 else 's'}"


def points_text(points):
    """A balance as a member reads it, negative included: "240 points", "1 point", "-67 points"."""
    return f"{points} point{'' if points == 1 else 's'}"


def spend_block(points):
    """Why nothing can be spent at this balance, or blank if something can."""
    if points < 0:
        return f"You're at {points_text(points)}. {SPENDING_BLOCKED}"
    return "" if points else "You have no points to spend."
