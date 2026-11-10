import json
import re
from pathlib import Path

import pytest
from django.urls import reverse

ROOT = Path(__file__).resolve().parents[2]

TABS = [
    ("/", "Home"),
    ("/currently/", "Currently"),
    ("/library/", "Library"),
    ("/feed/", "Feed"),
]


@pytest.mark.django_db
@pytest.mark.parametrize(("path", "label"), TABS)
def test_each_tab_renders_with_the_shell(member_client, path, label):
    response = member_client.get(path)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Search movies, TV, anime, manga" in html
    assert 'aria-label="Quick log"' in html
    assert 'aria-current="page"' in html
    # The active tab is the one we asked for.
    active = re.search(r'<a[^>]*aria-current="page"[^>]*>(.*?)</a>', html, re.S)
    assert label in active.group(1)


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/currently/", "/library/", "/feed/"])
def test_empty_tabs_show_a_designed_empty_state(member_client, path):
    html = member_client.get(path).content.decode()
    assert 'class="empty"' in html


@pytest.mark.django_db
def test_home_renders_the_carousel_shell(member_client):
    html = member_client.get("/").content.decode()
    assert html.count('class="carousel"') >= 3


@pytest.mark.django_db
def test_header_shows_the_cog_on_the_profile(member_client):
    html = member_client.get("/me/").content.decode()
    assert 'aria-label="Settings"' in html
    assert reverse("member:settings") in html


@pytest.mark.django_db
def test_base_has_title_meta_favicon_and_manifest(member_client):
    html = member_client.get("/").content.decode()
    assert "<title>" in html
    assert 'name="viewport"' in html
    assert 'name="theme-color"' in html
    assert 'rel="manifest"' in html
    assert 'rel="icon"' in html
    assert 'rel="apple-touch-icon"' in html


@pytest.mark.django_db
def test_manifest_is_public_valid_json(client):
    response = client.get("/manifest.json")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["name"] == "MediaTracker"
    assert data["display"] == "standalone"
    assert data["background_color"].lower() == "#121315"
    assert any(i["sizes"] == "512x512" for i in data["icons"])


@pytest.mark.django_db
def test_about_page_carries_tmdb_attribution(member_client):
    html = member_client.get(reverse("core:about")).content.decode()
    assert "This product uses the TMDB API but is not endorsed or certified by TMDB." in html
    assert "tmdb-logo" in html


@pytest.mark.django_db
def test_footer_carries_tmdb_attribution_on_every_tab(member_client):
    for path, _ in TABS:
        html = member_client.get(path).content.decode()
        assert "not endorsed or certified by TMDB" in html


@pytest.mark.django_db
def test_404_is_designed_and_in_the_shell(member_client):
    response = member_client.get("/definitely/not/here/")
    assert response.status_code == 404
    html = response.content.decode()
    assert "Page not found" in html
    assert 'aria-label="Main"' in html


@pytest.mark.django_db
def test_404_for_anonymous_has_no_member_shell(client):
    response = client.get("/definitely/not/here/")
    assert response.status_code in (302, 404)
    if response.status_code == 404:
        assert 'aria-label="Main"' not in response.content.decode()


def test_500_template_is_standalone():
    html = (ROOT / "core/templates/500.html").read_text()
    assert "extends" not in html
    assert "Something broke" in html


@pytest.mark.django_db
def test_htmx_and_fonts_are_self_hosted(member_client):
    html = member_client.get("/").content.decode()
    assert "htmx.min.js" in html
    assert "unpkg" not in html
    assert "fonts.googleapis" not in html
    assert "cdn" not in html.lower()


# Outbound credit links on the About page. They are links a member can follow, not anything the
# page loads, so they are listed by exact address and only for that one template.
ABOUT_CREDITS = {
    "https://myanimelist.net",
    "https://anilist.co",
    "https://github.com/Fribb/anime-lists",
}


def test_no_template_loads_anything_from_a_third_party_host():
    offenders = []
    for path in ROOT.glob("*/templates/**/*.html"):
        for url in re.findall(r'(?:src|href)="(https?://[^"]+)"', path.read_text()):
            if "themoviedb.org" in url or (path.name == "about.html" and url in ABOUT_CREDITS):
                continue
            offenders.append((path.name, url))
    assert offenders == []


@pytest.mark.django_db
def test_quick_log_sheet_markup_is_an_accessible_dialog(member_client):
    html = member_client.get("/").content.decode()
    assert 'id="sheet-host"' in html  # where the server-sent sheet is opened
    response = member_client.get(reverse("core:quick_log"))
    assert response.status_code == 200
    assert 'role="dialog"' in response.content.decode()


@pytest.mark.django_db
def test_search_page_renders_with_query(member_client):
    response = member_client.get(reverse("core:search"), {"q": "dune"})
    assert response.status_code == 200
    assert "dune" in response.content.decode()


@pytest.mark.django_db
def test_admin_sees_manage_link_in_settings_but_member_does_not(admin_client, member_client):
    assert "/manage/" in admin_client.get("/settings/").content.decode()
    assert "/manage/" not in member_client.get("/settings/").content.decode()
    assert "/manage/" not in member_client.get("/me/").content.decode()


@pytest.mark.django_db
def test_security_headers_and_cookies(member_client, settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert member_client.get("/").headers["X-Frame-Options"] == "DENY"
    assert member_client.get("/").headers["Cache-Control"].startswith("private") or (
        "no-store" in member_client.get("/").headers.get("Cache-Control", "")
    )


def test_production_cookies_are_secure_when_debug_is_off():
    import subprocess
    import sys

    code = (
        "import os, django;"
        "os.environ['DJANGO_SETTINGS_MODULE']='config.settings';"
        "os.environ['DEBUG']='0';"
        "from django.conf import settings;"
        "print(settings.SESSION_COOKIE_SECURE, settings.CSRF_COOKIE_SECURE)"
    )
    out = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, check=True
    )
    assert out.stdout.split() == ["True", "True"]


@pytest.mark.django_db
@pytest.mark.urls("core.tests.urls_boom")
def test_server_error_renders_the_standalone_page(member):
    from django.test import Client

    client = Client(raise_request_exception=False)
    client.force_login(member)
    response = client.get("/boom/")
    assert response.status_code == 500
    html = response.content.decode()
    assert "Something broke" in html
    assert "<link" not in html  # needs no static files
