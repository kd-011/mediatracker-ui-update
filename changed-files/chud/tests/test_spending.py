"""Buying and gifting. The price comes from the catalogue and nowhere else."""

import pytest

from chud import selectors, services
from chud.models import ChudLedger, StickerGift, UserSticker
from social import services as social

from .conftest import balance

pytestmark = pytest.mark.django_db


def owned(user, sticker):
    return UserSticker.objects.filter(user=user, sticker=sticker).values_list("count", flat=True)


def latest(user):
    return ChudLedger.objects.filter(user=user).order_by("-pk").first()


@pytest.fixture
def post(other, make_post, season):
    from tracking import services as tracking

    tracking.log_up_to(other, season, 10)
    return make_post(other, season)


@pytest.fixture
def comment(post, other):
    return social.add_comment(post, other, "Agreed")


# Buying


def test_buying_spends_the_price_and_adds_one(member, give):
    give(member, points=240)
    services.buy_sticker(member, "cooked")
    assert balance(member) == (140, 0)
    assert list(owned(member, "cooked")) == [1]
    services.buy_sticker(member, "cooked")
    assert list(owned(member, "cooked")) == [2]
    row = latest(member)
    assert (row.kind, row.points, row.xp) == (ChudLedger.Kind.BUY, -100, 0)
    assert row.text == "Bought Cooked"
    assert row.sticker == "cooked"


def test_buying_with_too_few_points_is_refused_and_changes_nothing(member, give):
    give(member, points=99)
    before = ChudLedger.objects.count()
    with pytest.raises(services.ChudError, match="1 more point"):
        services.buy_sticker(member, "cooked")
    assert balance(member) == (99, 0)
    assert not owned(member, "cooked")
    assert ChudLedger.objects.count() == before


def test_buying_with_exactly_enough_leaves_nothing(member, give):
    give(member, points=500)
    services.buy_sticker(member, "cinema")
    assert balance(member)[0] == 0


def test_a_sticker_that_does_not_exist_is_refused(member, give):
    give(member, points=500)
    with pytest.raises(services.ChudError):
        services.buy_sticker(member, "free-money")


def test_buying_with_no_account_yet_is_refused_not_a_crash(member):
    with pytest.raises(services.ChudError):
        services.buy_sticker(member, "grass")


def test_the_same_token_buys_once_and_a_new_one_buys_again(member, give):
    give(member, points=300)
    services.buy_sticker(member, "cooked", token="a")
    services.buy_sticker(member, "cooked", token="a")
    assert balance(member)[0] == 200
    assert list(owned(member, "cooked")) == [1]
    services.buy_sticker(member, "cooked", token="b")
    assert balance(member)[0] == 100


def test_a_token_belongs_to_one_member(member, other, give):
    give(member, points=100)
    give(other, points=100)
    services.buy_sticker(member, "cooked", token="a")
    services.buy_sticker(other, "cooked", token="a")
    assert balance(other)[0] == 0


# Gifting


@pytest.mark.parametrize(
    "sticker,price,payout",
    [
        ("grass", 50, 35),
        ("cooked", 100, 70),
        ("sleep", 150, 105),
        ("peak", 250, 175),
        ("cinema", 500, 350),
    ],
)
def test_buy_and_send_pays_the_price_and_the_friend_gets_seventy_percent(
    member, other, post, give, sticker, price, payout
):
    give(member, points=500)
    gift = services.send_sticker(member, post, sticker)
    assert balance(member)[0] == 500 - price
    assert balance(other)[0] >= payout
    assert (gift.sender, gift.recipient, gift.post, gift.comment) == (member, other, post, None)
    assert (gift.price_paid, gift.payout) == (price, payout)
    assert list(owned(other, sticker)) == [1]


def test_a_gift_writes_both_sides_of_the_ledger(member, other, post, give):
    give(member, points=100)
    gift = services.send_sticker(member, post, "cooked")
    mine = latest(member)
    theirs = latest(other)
    assert (mine.kind, mine.points, mine.text) == (
        ChudLedger.Kind.GIFT_SENT,
        -100,
        "Sent Cooked to Kev",
    )
    assert (theirs.kind, theirs.points, theirs.text) == (
        ChudLedger.Kind.GIFT_RECEIVED,
        70,
        "Maya sent you Cooked",
    )
    assert mine.counterparty == other and theirs.counterparty == member
    assert mine.gift == gift and theirs.gift == gift


def test_received_points_add_no_xp(member, other, post, give):
    give(member, points=100)
    before = balance(other)[1]
    services.send_sticker(member, post, "cooked")
    assert balance(other)[1] == before


def test_sending_from_the_collection_costs_no_points_and_pays_the_same(member, other, post, give):
    give(member, points=100)
    services.buy_sticker(member, "cooked")
    before = balance(other)[0]
    gift = services.send_sticker(member, post, "cooked", from_collection=True)
    assert balance(member)[0] == 0
    assert list(owned(member, "cooked")) == [0]
    assert balance(other)[0] == before + 70
    assert gift.price_paid == 0 and gift.payout == 70
    assert (latest(member).points, latest(member).text) == (0, "Sent Cooked to Kev")


def test_sending_from_an_empty_collection_is_refused_and_never_charges(member, other, post, give):
    give(member, points=500)
    with pytest.raises(services.ChudError, match="don't have"):
        services.send_sticker(member, post, "cooked", from_collection=True)
    assert balance(member)[0] == 500
    assert not StickerGift.objects.exists()


def test_buy_and_send_with_too_few_points_is_refused(member, other, post, give):
    give(member, points=99)
    before = balance(other)
    with pytest.raises(services.ChudError):
        services.send_sticker(member, post, "cooked")
    assert balance(member)[0] == 99
    assert balance(other) == before
    assert not StickerGift.objects.exists()


def test_a_gift_can_go_on_a_comment(member, other, comment, give):
    give(member, points=50)
    gift = services.send_sticker(member, comment, "grass")
    assert gift.comment == comment and gift.post is None
    assert gift.recipient == other


def test_you_cannot_gift_your_own_post_or_comment(other, post, comment, give):
    give(other, points=500)
    before = balance(other)
    for target in (post, comment):
        with pytest.raises(services.ChudError, match="your own"):
            services.send_sticker(other, target, "grass")
    assert balance(other) == before


def test_a_deactivated_member_cannot_be_sent_anything(member, other, post, give):
    give(member, points=500)
    other.is_active = False
    other.save()
    with pytest.raises(services.ChudError):
        services.send_sticker(member, post, "grass")
    assert balance(member)[0] == 500


def test_the_same_gift_sent_twice_is_one_gift(member, other, post, give):
    give(member, points=500)
    before = balance(other)[0]
    first = services.send_sticker(member, post, "cooked", token="t")
    second = services.send_sticker(member, post, "cooked", token="t")
    assert first == second
    assert StickerGift.objects.count() == 1
    assert balance(member)[0] == 400
    assert balance(other)[0] == before + 70


def test_a_gift_token_that_also_bought_something_is_still_one_of_each(member, post, give):
    give(member, points=500)
    services.buy_sticker(member, "cooked", token="t")
    services.send_sticker(member, post, "cooked", token="t")
    assert balance(member)[0] == 300


def test_deleting_the_post_keeps_the_points_and_the_ledger(member, other, post, give):
    give(member, points=100)
    services.send_sticker(member, post, "cooked")
    theirs = balance(other)[0]
    social.delete_post(post)
    assert not StickerGift.objects.exists()
    assert balance(other)[0] == theirs
    assert latest(other).text == "Maya sent you Cooked"
    assert latest(other).gift is None


# While the balance is not positive


@pytest.fixture
def negative(member, give):
    give(member, points=-67)
    return member


@pytest.mark.parametrize("points", [-67, 0])
def test_buying_is_refused_while_the_balance_is_not_positive(member, give, points):
    give(member, points=points)
    with pytest.raises(services.ChudError, match="blocked|no points"):
        services.buy_sticker(member, "grass")
    assert balance(member)[0] == points
    assert not owned(member, "grass")


@pytest.mark.parametrize("points", [-67, 0])
def test_buy_and_send_is_refused_while_the_balance_is_not_positive(
    member, other, post, give, points
):
    give(member, points=points)
    before = balance(other)
    with pytest.raises(services.ChudError, match="blocked|no points"):
        services.send_sticker(member, post, "grass")
    assert balance(member)[0] == points
    assert balance(other) == before
    assert not StickerGift.objects.exists()


@pytest.mark.parametrize("points", [-67, 0])
def test_a_bounty_is_refused_while_the_balance_is_not_positive(member, other, season, give, points):
    from chud.models import Bounty

    give(member, points=points)
    with pytest.raises(services.ChudError, match="blocked|no points"):
        services.place_bounty(member, other, season, 1)
    assert balance(member)[0] == points
    assert not Bounty.objects.exists()


def test_every_debit_goes_through_the_one_check(member, monkeypatch):
    """Nothing priced at 0 can slip through, because the check doesn't start from the price."""
    account = services._accounts(member.pk)[member.pk]
    account.points = -1
    with pytest.raises(services.ChudError, match="blocked"):
        services._debit(account, ChudLedger.Kind.BUY, "Free", 0)
    account.points = 0
    with pytest.raises(services.ChudError, match="no points"):
        services._debit(account, ChudLedger.Kind.BUY, "Free", 0)


def test_sending_a_sticker_you_own_is_not_spending_so_it_stays_allowed(member, other, post, give):
    give(member, points=100)
    services.buy_sticker(member, "cooked")
    give(member, points=-67)
    before = balance(other)[0]
    services.send_sticker(member, post, "cooked", from_collection=True)
    assert balance(member)[0] == -67
    assert balance(other)[0] == before + 70
    assert list(owned(other, "cooked")) == [1]


def test_a_refund_still_applies_while_negative_and_can_unblock(member, other, season, give):
    give(member, points=100)
    bounty = services.place_bounty(member, other, season, 100)
    give(member, points=-67)
    services.cancel_bounty(bounty, member)
    assert balance(member)[0] == 33
    with pytest.raises(services.ChudError, match="17 more points"):
        services.buy_sticker(member, "grass")


def test_a_gift_received_still_applies_while_negative(
    member, other, third, make_post, season, give
):
    from tracking import services as tracking

    tracking.log_up_to(member, season, 10)
    mine = make_post(member, season)
    points = balance(member)[0]
    give(member, points=-points - 10)
    give(other, points=100)
    services.send_sticker(other, mine, "cooked")
    assert balance(member)[0] == 60


def test_a_credit_that_returns_the_balance_to_positive_unblocks_spending(negative, give):
    with pytest.raises(services.ChudError):
        services.buy_sticker(negative, "grass")
    give(negative, points=67)
    with pytest.raises(services.ChudError, match="no points"):
        services.buy_sticker(negative, "grass")
    give(negative, points=50)
    services.buy_sticker(negative, "grass")
    assert balance(negative)[0] == 0


# Stickers on the page


def test_stickers_on_groups_by_sticker_in_catalogue_order(member, third, post, comment, give):
    from social.stickers import stickers_on

    give(member, points=1000)
    give(third, points=1000)
    for sender, sticker in ((member, "cooked"), (third, "cooked"), (member, "grass")):
        services.send_sticker(sender, post, sticker)
    services.send_sticker(member, comment, "peak")
    found = stickers_on("post", [post.pk])[post.pk]
    assert [(s["name"], s["count"], s["aria"]) for s in found] == [
        ("Touch Grass", 1, "Touch Grass, 1"),
        ("Cooked", 2, "Cooked, 2"),
    ]
    assert found[0]["bg"] and found[0]["fg"] and found[0]["d"]
    assert stickers_on("comment", [comment.pk])[comment.pk][0]["name"] == "Peak"
    assert stickers_on("post", [post.pk + 1]) == {}


# Buddies


def test_a_locked_buddy_cannot_be_chosen(member):
    with pytest.raises(services.ChudError, match="level 5"):
        services.set_buddy(member, "goblin")
    assert selectors.active_buddy(member) is None


def test_an_unlocked_buddy_can_be_chosen(member, give):
    give(member, xp=1000)
    services.set_buddy(member, "goblin")
    member.refresh_from_db()
    assert member.chud_buddy == "goblin"
    assert selectors.active_buddy(member).id == "goblin"


def test_a_buddy_that_does_not_exist_is_refused(member, give):
    give(member, xp=100000)
    with pytest.raises(services.ChudError):
        services.set_buddy(member, "dragon")
