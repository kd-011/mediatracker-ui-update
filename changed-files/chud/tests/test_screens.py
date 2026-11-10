"""Profile, store, gift sheet, level-up sheet and bounty sheet, as a member gets them."""

import json
import re

import pytest
from django.urls import reverse

from chud import selectors, services
from chud.models import ChudLedger, UserSticker
from social import services as social
from tracking import services as tracking

from .conftest import DAY, balance

pytestmark = pytest.mark.django_db


def me(client):
    return client.get(reverse("accounts:me"), follow=True)


def trigger(response):
    return json.loads(response.get("HX-Trigger", "{}"))


def tag_for(html, text):
    """The opening tag of the button whose aria-label is this."""
    found = re.search(rf'<button[^>]*aria-label="{re.escape(text)}"[^>]*>', html)
    assert found, text
    return found.group(0)


@pytest.fixture
def post(other, make_post, season):
    tracking.log_up_to(other, season, 10, on=DAY)
    return make_post(other, season)


@pytest.fixture
def comment(post, other):
    return social.add_comment(post, other, "Agreed")


# Profile


def test_my_profile_shows_level_points_and_xp_line(member, member_client, give):
    give(member, points=240, xp=4460)
    html = me(member_client).text
    assert "CHUD level 9" in html
    assert "240 points" in html
    assert "4,460 XP. 40 to level 10. New buddy at level 10" in html
    assert "width: 96%" in html


def test_a_new_member_sees_nothing_broken(member_client):
    html = me(member_client).text
    assert "CHUD level 1" in html
    assert "0 points" in html
    assert "0 XP. 100 to level 2. New buddy at level 5" in html
    assert "No stickers yet." in html
    assert "New buddy at level 5" in html
    assert "Couch Goblin joins you at level 5" in html
    assert "Nothing yet" in html


def test_the_buddy_picker_shows_locked_active_and_set(member, member_client, give):
    give(member, xp=4500)
    services.set_buddy(member, "goblin")
    html = me(member_client).text
    goblin = tag_for(html, "Couch Goblin, your CHUD buddy")
    assert 'aria-pressed="true"' in goblin
    assert re.search(r'aria-label="Couch Goblin, your CHUD buddy".*?>\s*Couch Goblin\s*</button>', html, re.S)
    gremlin = tag_for(html, "Set Screen Gremlin as your CHUD buddy")
    assert 'aria-pressed="false"' in gremlin and "disabled" not in gremlin
    beast = tag_for(html, "Binge Beast, unlocks at level 15")
    assert "disabled" in beast
    assert "Level 15" in html and "Level 20" in html


def test_my_stickers_and_the_store_link(member, member_client, give):
    give(member, points=1000)
    services.buy_sticker(member, "grass")
    services.buy_sticker(member, "grass")
    html = me(member_client).text
    assert 'aria-label="Touch Grass, 2"' in html
    assert "No stickers yet." not in html
    assert reverse("chud:store") not in html


def test_recent_activity_shows_the_latest_twelve_newest_first(member, member_client, give):
    give(member, points=1200)
    for sticker in ("grass", "cooked", "sleep", "peak", "cinema", "grass", "grass"):
        services.buy_sticker(member, sticker)
    html = me(member_client).text
    section = html.split("CHUD activity")[1]
    assert section.count('class="chud-activity__row"') == 7
    assert section.index("Bought Touch Grass") < section.index("Bought Absolute Cinema")
    assert "Bought Cooked" in section
    assert "Test money" not in section
    assert "-500" in section


def test_activity_marks_a_gift_from_the_collection(member, member_client, give, post):
    give(member, points=100)
    services.buy_sticker(member, "cooked")
    services.send_sticker(member, post, "cooked", from_collection=True)
    section = me(member_client).text.split("CHUD activity")[1]
    assert "Sent Cooked to Kev" in section
    assert "From collection" in section


def test_a_received_gift_shows_with_a_plus(
    member, member_client, other, third, give, make_post, movie
):
    tracking.log_unit(member, movie, on=DAY)
    mine = make_post(member, movie)
    give(other, points=100)
    services.send_sticker(other, mine, "cooked")
    section = me(member_client).text.split("CHUD activity")[1]
    assert "Kev sent you Cooked" in section
    assert "+70" in section


def test_someone_elses_profile_shows_level_and_buddy_but_not_their_wallet(
    member, member_client, other, give
):
    give(other, points=4321, xp=1000)
    services.buy_sticker(other, "grass")
    services.set_buddy(other, "goblin")
    html = member_client.get(reverse("social:profile", args=["kev"])).text
    assert "CHUD level 5" in html
    assert "Couch Goblin" in html
    assert "4221" not in html
    assert "Your stickers" not in html
    assert "CHUD activity" not in html
    assert "Open CHUD store" not in html
    assert "Bought" not in html


def test_a_private_members_profile_shows_no_chud_at_all(member_client, other, give):
    give(other, xp=1000)
    services.set_buddy(other, "goblin")
    other.default_visibility = "private"
    other.save()
    html = member_client.get(reverse("social:profile", args=["kev"])).text
    assert "CHUD level" not in html
    assert "Couch Goblin" not in html


def test_the_crown_shows_on_the_winners_profile_until_replaced(member, member_client, other, movie):
    from datetime import date

    tracking.log_unit(other, movie, on=date(2026, 10, 19))
    services.decide_week(date(2026, 10, 26))
    assert "Chud of the Week" in member_client.get(reverse("social:profile", args=["kev"])).text
    assert "Chud of the Week" not in me(member_client).text


def test_choosing_a_buddy_answers_with_the_picker(member, member_client, give):
    give(member, xp=4500)
    response = member_client.post(reverse("chud:buddy"), {"buddy": "gremlin"})
    assert response.status_code == 200
    assert 'id="chud-buddy"' in response.text and "hx-swap-oob" in response.text
    member.refresh_from_db()
    assert member.chud_buddy == "gremlin"


def test_choosing_a_locked_buddy_is_refused_with_the_reason(member_client):
    response = member_client.post(reverse("chud:buddy"), {"buddy": "final"})
    assert response.status_code == 400
    assert "level 20" in response.text


# A negative balance


def test_the_profile_shows_a_negative_balance_as_it_is(member, member_client, give):
    give(member, points=-67)
    html = me(member_client).text
    assert "-67 points" in html
    assert "is-negative" in html


def test_one_point_is_one_point(member, member_client, give):
    give(member, points=1)
    assert ">1 point<" in me(member_client).text


def test_the_store_says_why_spending_is_blocked(member, member_client, give):
    give(member, points=-67)
    html = member_client.get(reverse("chud:store")).text
    assert "-67 points" in html
    assert "to spend" not in html.split("CHUD store")[-1].split("When you send")[0]
    assert "Spending is blocked until you&#x27;re back above zero." in html
    assert "disabled" in tag_for(html, "Buy Touch Grass for 50 points")
    assert "more points needed" not in html


def test_buying_while_negative_is_refused_over_http(member, member_client, give):
    give(member, points=-67)
    response = member_client.post(reverse("chud:buy"), {"sticker": "grass", "token": "a"})
    assert response.status_code == 400
    assert "blocked" in response.text
    assert balance(member)[0] == -67


def test_the_gift_sheet_while_negative_only_offers_what_you_own(member, member_client, give, post):
    give(member, points=100)
    services.buy_sticker(member, "cooked")
    give(member, points=-67)
    html = member_client.get(reverse("chud:gift_post", args=[post.pk])).text
    assert "-67 points" in html
    assert "Spending is blocked" in html
    assert "disabled" not in tag_for(html, "Send Cooked")
    assert "disabled" in tag_for(html, "Buy and send Touch Grass")


def test_the_bounty_sheet_while_negative_says_why_and_is_disabled(
    member, member_client, other, give, movie
):
    give(member, points=-67)
    html = member_client.get(reverse("chud:bounty_new", args=[movie.pk])).text
    assert "Spending is blocked until you&#x27;re back above zero." in html
    assert "Spending blocked</button>" in html
    response = member_client.post(
        reverse("chud:bounty_new", args=[movie.pk]),
        {"recipient": other.username, "amount": "1", "token": "t"},
    )
    assert response.status_code == 400
    assert "Spending is blocked" in response.text
    assert balance(member)[0] == -67


# Store


def test_the_store_lists_every_sticker_with_price_and_note(member, member_client, give):
    give(member, points=240)
    services.buy_sticker(member, "grass")
    html = member_client.get(reverse("chud:store")).text
    assert "CHUD store" in html
    assert "190 points to spend" in html
    assert "When you send a sticker, your friend gets 70% of its price in points." in html
    assert "You own 1" in html
    assert "Friend gets 70 points" in html
    for label in ("50 pts", "100 pts", "150 pts", "250 pts", "500 pts"):
        assert label in html
    assert "Back to profile" in html


def test_a_sticker_too_dear_is_disabled_and_says_why(member, member_client, give):
    give(member, points=240)
    html = member_client.get(reverse("chud:store")).text
    assert "disabled" in tag_for(html, "Buy Absolute Cinema for 500 points")
    assert "260 more points needed" in html
    assert "disabled" not in tag_for(html, "Buy Touch Grass for 50 points")


def test_buying_answers_with_the_new_state(member, member_client, give):
    give(member, points=100)
    response = member_client.post(reverse("chud:buy"), {"sticker": "cooked", "token": "a"})
    assert response.status_code == 200
    assert trigger(response)["toast"]["value"] == "Added Cooked to your stickers"
    assert 'id="store-points"' in response.text
    assert "0 points to spend" in response.text
    assert 'id="store-row-cooked"' in response.text
    assert "You own 1" in response.text
    assert balance(member)[0] == 0


def test_the_price_comes_from_the_catalogue_not_the_request(member, member_client, give):
    give(member, points=100)
    member_client.post(
        reverse("chud:buy"), {"sticker": "cooked", "price": "1", "amount": "1", "points": "1"}
    )
    assert balance(member)[0] == 0


def test_a_refused_purchase_says_why_and_changes_nothing(member, member_client, give):
    give(member, points=10)
    response = member_client.post(reverse("chud:buy"), {"sticker": "cinema", "token": "a"})
    assert response.status_code == 400
    assert "490 more points" in response.text
    assert balance(member)[0] == 10


def test_buying_needs_a_post(member_client):
    assert member_client.get(reverse("chud:buy")).status_code == 405


# Gift sheet


def test_the_gift_button_is_on_other_peoples_posts_only(
    member, member_client, other_client, post, comment
):
    html = member_client.get(reverse("social:post", args=[post.pk])).text
    assert 'aria-label="Send Kev a sticker"' in html
    assert reverse("chud:gift_post", args=[post.pk]) in html
    assert reverse("chud:gift_comment", args=[comment.pk]) in html
    mine = other_client.get(reverse("social:post", args=[post.pk])).text
    assert "a sticker" not in mine
    assert reverse("chud:gift_post", args=[post.pk]) not in mine
    assert reverse("chud:gift_comment", args=[comment.pk]) not in mine


def test_the_gift_sheet_offers_owned_and_buyable(member, member_client, give, post):
    give(member, points=240)
    services.buy_sticker(member, "cooked")
    html = member_client.get(reverse("chud:gift_post", args=[post.pk])).text
    assert "Send Kev a sticker" in html
    assert "140 points" in html
    assert "You own 1. Kev gets 70 points" in html
    assert "Kev gets 35 points" in html
    assert "disabled" not in tag_for(html, "Send Cooked")
    assert "disabled" in tag_for(html, "Buy and send Absolute Cinema")
    assert "360 more points needed" in html
    assert "disabled" not in tag_for(html, "Buy and send Touch Grass")
    assert 'name="token"' in html
    assert reverse("chud:store") in html


def test_sending_answers_with_the_sticker_and_a_toast(member, member_client, give, post):
    give(member, points=100)
    response = member_client.post(
        reverse("chud:gift_post", args=[post.pk]),
        {"sticker": "cooked", "token": "t", "pay": "buy"},
    )
    assert response.status_code == 200
    assert trigger(response)["toast"]["value"] == "Kev got 70 CHUD points"
    assert "sheet-close" in trigger(response)
    assert f'id="stickers-post-{post.pk}"' in response.text
    assert 'aria-label="Cooked, 1"' in response.text


def test_sending_on_a_comment_answers_with_its_slot(member, member_client, give, comment):
    give(member, points=50)
    response = member_client.post(
        reverse("chud:gift_comment", args=[comment.pk]),
        {"sticker": "grass", "token": "t", "pay": "buy"},
    )
    assert response.status_code == 200
    assert f'id="stickers-comment-{comment.pk}"' in response.text


def test_a_sticker_shows_under_the_post_and_comment_after_a_reload(
    member, member_client, third_client, give, post, comment
):
    give(member, points=1000)
    services.send_sticker(member, post, "cooked")
    services.send_sticker(member, post, "cooked")
    services.send_sticker(member, comment, "grass")
    html = third_client.get(reverse("social:post", args=[post.pk])).text
    assert 'aria-label="Cooked, 2"' in html
    assert 'aria-label="Touch Grass, 1"' in html


def test_a_post_you_may_not_see_cannot_be_gifted(member, member_client, give, post, other):
    give(member, points=100)
    social.set_account_visibility(other, "private")
    url = reverse("chud:gift_post", args=[post.pk])
    assert member_client.get(url).status_code == 404
    response = member_client.post(url, {"sticker": "cooked", "token": "t", "pay": "buy"})
    assert response.status_code == 404
    assert balance(member)[0] == 100


def test_gifting_your_own_post_over_http_is_refused(other, other_client, give, post):
    give(other, points=100)
    before = balance(other)[0]
    response = other_client.post(
        reverse("chud:gift_post", args=[post.pk]), {"sticker": "grass", "token": "t", "pay": "buy"}
    )
    assert response.status_code == 400
    assert balance(other)[0] == before


def test_the_gift_sheet_for_your_own_post_is_refused(other_client, post):
    assert other_client.get(reverse("chud:gift_post", args=[post.pk])).status_code == 403


def test_a_stale_sheet_cannot_charge_for_a_sticker_it_said_was_free(
    member, member_client, give, post
):
    give(member, points=500)
    response = member_client.post(
        reverse("chud:gift_post", args=[post.pk]),
        {"sticker": "cooked", "token": "t", "pay": "owned"},
    )
    assert response.status_code == 400
    assert balance(member)[0] == 500


# Earning, as the member sees it


def test_a_plus_one_says_what_it_earned_and_keeps_its_own_toast(member, member_client, season):
    response = member_client.post(reverse("tracking:log", args=[season.pk]), {"n": 1, "quiet": 1})
    events = trigger(response)
    assert events["toast"]["value"] == "Episode 1 logged"
    amount = balance(member)[0]
    assert events["chud-earned"]["value"] == f"+{amount} CHUD points and XP"


def test_what_a_log_earned_can_show_above_the_rate_sheet_a_plus_one_opens(member_client):
    """A modal covers the page's toasts, and on TV and anime a +1 opens one every time."""
    from pathlib import Path

    from django.conf import settings

    html = member_client.get(reverse("core:home")).text
    assert 'id="toasts-over"' in html and 'popover="manual"' in html
    script = Path(settings.BASE_DIR, "core/static/core/js/app.js").read_text()
    handler = script.split('"chud-earned"')[1].split("\n  });")[0]
    assert "dialog[open]" in handler and "over.showPopover();" in handler


def test_a_write_that_changes_nothing_says_nothing(member, member_client, season):
    url = reverse("tracking:log", args=[season.pk])
    member_client.post(url, {"n": 1, "quiet": 1})
    assert "chud-earned" not in trigger(member_client.post(url, {"n": 1, "quiet": 1}))


def test_undo_says_nothing_about_points(member, member_client, season):
    member_client.post(reverse("tracking:log", args=[season.pk]), {"n": 1, "quiet": 1})
    response = member_client.post(reverse("tracking:undo", args=[season.pk]), {"n": 1})
    assert "chud-earned" not in trigger(response)


def test_collecting_a_bounty_says_so(member, member_client, other, give, movie):
    give(other, points=50)
    services.place_bounty(other, member, movie, 50)
    response = member_client.post(reverse("tracking:log", args=[movie.pk]))
    assert "bounty" in trigger(response)["chud-earned"]["value"]


# Level up


def test_crossing_a_buddy_level_raises_the_sheet(member, member_client, give, season):
    give(member, xp=995)
    response = member_client.post(reverse("tracking:log", args=[season.pk]), {"n": 1, "quiet": 1})
    assert trigger(response)["chud-level-up"]["url"] == reverse("chud:level_up")


def test_the_level_up_sheet_matches_the_prototype(member, member_client, give):
    give(member, xp=1000)
    services.answer_level_up(member, equip=False)
    from chud.models import ChudAccount

    ChudAccount.objects.filter(user=member).update(pending_buddy="goblin")
    html = member_client.get(reverse("chud:level_up")).text
    assert "CHUD level 5" in html
    assert "Couch Goblin" in html
    assert "A new CHUD buddy you can only get by levelling up." in html
    assert "Make it my CHUD buddy" in html
    # Nobody to keep yet: the prototype only ever shows this with a buddy already on.
    assert "Keep my current buddy" not in html
    assert "Not now" in html
    services.set_buddy(member, "goblin")
    assert "Keep my current buddy" in member_client.get(reverse("chud:level_up")).text


def test_a_level_up_still_pending_is_offered_on_the_next_page(member, member_client, give, season):
    give(member, xp=995)
    tracking.log_unit(member, season, n=1, on=DAY)
    html = member_client.get(reverse("core:home")).text
    assert f'data-level-up="{reverse("chud:level_up")}"' in html


def test_equipping_from_the_sheet_and_dismissing_it(member, member_client, give, season):
    give(member, xp=995)
    tracking.log_unit(member, season, n=1, on=DAY)
    response = member_client.post(reverse("chud:level_up"), {"equip": "1"})
    assert response.status_code == 200
    assert "sheet-close" in trigger(response)
    member.refresh_from_db()
    assert member.chud_buddy == "goblin"
    assert selectors.account(member).pending_buddy == ""
    assert "data-level-up" not in member_client.get(reverse("core:home")).text


def test_dismissing_keeps_the_current_buddy(member, member_client, give, season):
    give(member, xp=995)
    tracking.log_unit(member, season, n=1, on=DAY)
    member_client.post(reverse("chud:level_up"), {"equip": "0"})
    member.refresh_from_db()
    assert member.chud_buddy == ""
    assert selectors.account(member).pending_buddy == ""


def test_answering_with_nothing_pending_is_harmless(member, member_client):
    assert member_client.post(reverse("chud:level_up"), {"equip": "1"}).status_code == 200
    assert member_client.get(reverse("chud:level_up")).status_code == 204


# Bounties


def test_a_title_page_offers_a_bounty(member_client, movie):
    html = member_client.get(reverse("catalogue:title", args=[movie.pk])).text
    assert reverse("chud:bounty_new", args=[movie.pk]) in html


def test_the_bounty_sheet_lists_who_can_get_one(member, member_client, other, third, give, movie):
    give(member, points=120)
    third.default_visibility = "private"
    third.save()
    html = member_client.get(reverse("chud:bounty_new", args=[movie.pk])).text
    assert "Kev" in html
    assert "Jimmy" not in html
    assert "120 points" in html
    assert 'name="token"' in html
    assert 'max="120"' in html


def test_setting_a_bounty_over_http(member, member_client, other, give, movie):
    give(member, points=100)
    response = member_client.post(
        reverse("chud:bounty_new", args=[movie.pk]),
        {"recipient": other.username, "amount": "40", "token": "t"},
    )
    assert response.status_code == 200
    assert "sheet-close" in trigger(response)
    assert "Kev" in trigger(response)["toast"]["value"]
    assert balance(member)[0] == 60


def test_a_refused_bounty_comes_back_with_what_was_typed(member, member_client, other, give, movie):
    give(member, points=10)
    response = member_client.post(
        reverse("chud:bounty_new", args=[movie.pk]),
        {"recipient": other.username, "amount": "40", "token": "t"},
    )
    assert response.status_code == 400
    assert "data-sheet" in response.text
    assert 'value="40"' in response.text
    assert "30 more points" in response.text
    assert balance(member)[0] == 10


def test_nonsense_in_the_bounty_form_is_refused(member, member_client, other, give, movie):
    give(member, points=100)
    url = reverse("chud:bounty_new", args=[movie.pk])
    assert (
        member_client.post(
            url, {"recipient": other.username, "amount": "lots", "token": "t"}
        ).status_code
        == 400
    )
    assert (
        member_client.post(url, {"recipient": "nobody", "amount": "5", "token": "t"}).status_code
        == 400
    )
    assert balance(member)[0] == 100


def test_my_profile_lists_bounties_on_me_and_ones_i_set(member, member_client, other, give, movie):
    give(member, points=100)
    give(other, points=100)
    mine = services.place_bounty(member, other, movie, 40)
    services.place_bounty(other, member, movie, 30)
    html = me(member_client).text
    assert "CHUD activity" in html
    assert "From Kev" in html and "30 points" in html
    assert "For Kev" in html and "40 points" in html
    assert reverse("chud:bounty_cancel", args=[mine.pk]) in html


def test_a_bounty_card_shows_the_time_left(member, member_client, other, give, movie):
    give(member, points=100)
    services.place_bounty(member, other, movie, 40)
    assert "d left" in me(member_client).text


def test_no_bounties_means_no_section(member_client):
    assert "Bounties" not in me(member_client).text


def test_someone_elses_bounties_are_not_on_their_profile(member_client, other, third, give, movie):
    give(other, points=100)
    services.place_bounty(other, third, movie, 40)
    assert "Bounties" not in member_client.get(reverse("social:profile", args=["kev"])).text


def test_cancelling_over_http(member, member_client, other, give, movie):
    give(member, points=100)
    bounty = services.place_bounty(member, other, movie, 40)
    response = member_client.post(reverse("chud:bounty_cancel", args=[bounty.pk]))
    assert response.status_code == 200
    assert balance(member)[0] == 100
    assert 'id="chud-bounties"' in response.text


def test_someone_elses_bounty_cannot_be_cancelled_or_even_found(
    member_client, other, third, give, movie
):
    give(other, points=100)
    bounty = services.place_bounty(other, third, movie, 40)
    assert member_client.post(reverse("chud:bounty_cancel", args=[bounty.pk])).status_code == 404
    assert balance(other)[0] == 60


def test_the_title_page_says_who_has_a_bounty_on_you(member, member_client, other, give, movie):
    give(other, points=100)
    services.place_bounty(other, member, movie, 40)
    html = member_client.get(reverse("catalogue:title", args=[movie.pk])).text
    assert "Kev has 40 points on you finishing this" in html


def test_csrf_is_enforced_on_buying(member, give):
    from django.test import Client

    give(member, points=100)
    client = Client(enforce_csrf_checks=True)
    client.force_login(member)
    assert client.post(reverse("chud:buy"), {"sticker": "cooked"}).status_code == 403
    assert balance(member)[0] == 100
    assert not UserSticker.objects.filter(user=member).exists()


def test_every_chud_page_needs_a_login(client, db):
    assert client.get(reverse("chud:store")).status_code == 302
    assert client.post(reverse("chud:buy"), {"sticker": "grass"}).status_code == 302


def test_no_prototype_demo_data_is_in_the_app_code():
    from pathlib import Path

    import chud

    base = Path(chud.__file__).parent
    for path in base.rglob("*"):
        if "tests" in path.parts or path.suffix not in (".py", ".html"):
            continue
        text = path.read_text()
        assert "Maya" not in text and "1000000" not in text, path


def test_seed_demo_million_xp_gives_the_prototypes_big_number(db):
    from django.core.management import call_command

    from accounts.models import User

    User.objects.create_user("shahan", "correct horse battery")
    call_command("seed_demo", "--library-for", "shahan", "--million-xp", "--force", verbosity=0)
    shahan = User.objects.get(username="shahan")
    assert selectors.account(shahan).xp == 1_000_000
    assert selectors.level(shahan) == 141
    assert ChudLedger.objects.filter(user=shahan, kind="adjust").exists()
    assert services.verify() == []


def test_seed_demo_without_the_flag_starts_at_the_prototypes_numbers(db):
    from django.core.management import call_command

    from accounts.models import User

    User.objects.create_user("shahan", "correct horse battery")
    call_command("seed_demo", "--library-for", "shahan", "--force", verbosity=0)
    shahan = User.objects.get(username="shahan")
    account = selectors.account(shahan)
    assert account.xp == 4460
    assert account.points == 240
    assert services.verify() == []
