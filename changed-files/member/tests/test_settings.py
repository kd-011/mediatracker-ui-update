"""The settings screen: preferences, password, buddy, export links, sign out."""

import pytest
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse

from accounts.models import User
from accounts.throttle import is_locked

pytestmark = pytest.mark.django_db

PASSWORD = "correct horse battery"
NEW = "a much better passphrase"


def page(client):
    return client.get(reverse("member:settings"))


def password(client, current=PASSWORD, new=NEW, again=None):
    return client.post(
        reverse("member:password"),
        {"current": current, "new": new, "again": new if again is None else again},
    )


def test_the_screen_needs_a_login(client):
    response = client.get(reverse("member:settings"))
    assert response.status_code == 302 and "/login/" in response["Location"]


def test_the_screen_has_every_section(member_client):
    html = page(member_client).content.decode()
    for text in (
        "Title language",
        "Show adult titles",
        "Default visibility",
        "Change password",
        "Me",
        "Export",
        "Delete account",
        "Sign out",
    ):
        assert text in html, text


def test_you_can_change_your_name_and_username(member, member_client):
    member_client.post(
        reverse("member:profile"), {"display_name": "Kye", "username": "kye"}
    )
    member.refresh_from_db()
    assert member.display_name == "Kye" and member.username == "kye"


def test_a_taken_username_is_refused(member, member_client, other):
    response = member_client.post(
        reverse("member:profile"), {"display_name": member.display_name, "username": other.username}
    )
    assert response.status_code == 200 and "username" in response.content.decode().lower()
    member.refresh_from_db()
    assert member.username != other.username


def test_the_screen_is_reached_from_the_profile(member_client):
    html = member_client.get(reverse("accounts:me")).content.decode()
    assert reverse("member:settings") in html


def test_sign_out_is_a_post_form(member_client):
    html = page(member_client).content.decode()
    assert f'action="{reverse("accounts:logout")}"' in html


def test_export_links_cover_every_file(member_client):
    html = page(member_client).content.decode()
    for kind in ("library.csv", "diary.csv", "episodes.csv", "anime.xml", "manga.xml"):
        assert reverse("member:export", args=[kind]) in html


def test_the_delete_link_goes_to_the_confirmation_page(member_client):
    assert reverse("member:delete") in page(member_client).content.decode()


# Preferences


def test_preferences_are_saved(member_client, member):
    response = member_client.post(
        reverse("member:preferences"),
        {"title_language": "romaji", "show_adult": "on", "default_visibility": "private"},
    )
    assert response.status_code == 302
    member.refresh_from_db()
    assert (member.title_language, member.show_adult, member.default_visibility) == (
        "romaji",
        True,
        "private",
    )


def test_an_unticked_adult_box_turns_it_off(member_client, member):
    User.objects.filter(pk=member.pk).update(show_adult=True)
    member_client.post(
        reverse("member:preferences"),
        {"title_language": "english", "default_visibility": "members"},
    )
    member.refresh_from_db()
    assert member.show_adult is False


@pytest.mark.parametrize(
    "data",
    [
        {"title_language": "klingon", "default_visibility": "members"},
        {"title_language": "english", "default_visibility": "everyone"},
        {"default_visibility": "members"},
    ],
)
def test_junk_is_refused_and_nothing_changes(member_client, member, data):
    response = member_client.post(reverse("member:preferences"), data)
    assert response.status_code == 200
    member.refresh_from_db()
    assert (member.title_language, member.default_visibility) == ("english", "members")


def test_a_preference_post_cannot_touch_other_fields(member_client, member):
    member_client.post(
        reverse("member:preferences"),
        {
            "title_language": "native",
            "default_visibility": "members",
            "is_admin": "on",
            "username": "root",
            "is_active": "",
        },
    )
    member.refresh_from_db()
    assert (member.is_admin, member.username, member.is_active) == (False, "maya", True)


def test_preferences_are_post_only(member_client):
    assert member_client.get(reverse("member:preferences")).status_code == 405


def test_the_language_changes_the_titles_members_see(member_client, member, anime):
    from catalogue.models import Media

    Media.objects.filter(pk=anime.pk).update(
        title_romaji="Sousou no Frieren", title_english="Frieren"
    )
    member_client.post(
        reverse("member:preferences"), {"title_language": "romaji", "default_visibility": "members"}
    )
    member.refresh_from_db()
    assert Media.objects.get(pk=anime.pk).title_for(member) == "Sousou no Frieren"


# Password


def test_the_password_changes_and_the_old_one_stops_working(member_client, member):
    assert password(member_client).status_code == 302
    member.refresh_from_db()
    assert member.check_password(NEW) and not member.check_password(PASSWORD)


def test_the_member_stays_signed_in_here_and_is_signed_out_elsewhere(member_client, member):
    phone = Client()
    phone.force_login(member)
    phone_key = phone.session.session_key
    password(member_client)
    assert not Session.objects.filter(session_key=phone_key).exists()  # before Django prunes it
    assert member_client.get("/").status_code == 200
    assert phone.get("/").status_code == 302
    assert Session.objects.count() >= 1


def test_the_current_password_is_required(member_client, member):
    response = password(member_client, current="guess guess guess")
    assert response.status_code == 200
    member.refresh_from_db()
    assert member.check_password(PASSWORD)


def test_a_weak_new_password_is_refused_with_the_reason(member_client, member):
    response = password(member_client, new="short")
    assert response.status_code == 200 and "too short" in response.content.decode()
    member.refresh_from_db()
    assert member.check_password(PASSWORD)


def test_the_two_new_passwords_must_match(member_client, member):
    assert password(member_client, again="something else entirely").status_code == 200
    member.refresh_from_db()
    assert member.check_password(PASSWORD)


def test_wrong_current_passwords_are_throttled(member_client, member, settings):
    for _ in range(settings.LOGIN_MAX_FAILURES):
        password(member_client, current="wrong wrong wrong")
    assert password(member_client).status_code == 429
    member.refresh_from_db()
    assert member.check_password(PASSWORD)
    assert is_locked("password-user", str(member.pk), settings.LOGIN_MAX_FAILURES)


def test_password_form_never_puts_passwords_back_in_the_page(member_client):
    html = password(member_client, current="wrong one here", new="x").content.decode()
    assert "wrong one here" not in html


# Buddy


def test_the_buddy_picker_is_not_on_settings(member_client):
    """The buddy lives on the profile; settings stays a settings screen."""
    assert reverse("chud:buddy") not in page(member_client).content.decode()
