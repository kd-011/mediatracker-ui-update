"""Avatars: uploaded, checked, re-encoded and served only to signed-in members."""

import io
import struct

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _avatar_dir(settings, tmp_path):
    settings.AVATAR_DIR = tmp_path / "avatars"


def picture(fmt="PNG", size=(600, 400), **save):
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 40, 40)).save(buffer, fmt, **save)
    return buffer.getvalue()


def upload(client, content, name="me.png", content_type="image/png"):
    return client.post(
        reverse("member:avatar"), {"file": SimpleUploadedFile(name, content, content_type)}
    )


def stored(settings):
    return (
        sorted(p.name for p in settings.AVATAR_DIR.glob("*"))
        if settings.AVATAR_DIR.exists()
        else []
    )


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
def test_a_picture_becomes_a_small_square_webp(member_client, member, settings, fmt):
    assert upload(member_client, picture(fmt)).status_code == 302
    member.refresh_from_db()
    assert member.avatar_path.endswith(".webp")
    with Image.open(settings.AVATAR_DIR / member.avatar_path) as saved:
        assert saved.format == "WEBP" and saved.size == (256, 256)


def test_exif_and_other_metadata_do_not_survive(member_client, member, settings):
    exif = Image.Exif()
    exif[0x010F] = "SecretCamera"
    exif[0x8825] = {1: "S", 2: (31.0, 0.0, 0.0)}
    buffer = io.BytesIO()
    Image.new("RGB", (300, 300)).save(buffer, "JPEG", exif=exif)
    upload(member_client, buffer.getvalue(), "p.jpg", "image/jpeg")
    member.refresh_from_db()
    raw = (settings.AVATAR_DIR / member.avatar_path).read_bytes()
    assert b"SecretCamera" not in raw and b"EXIF" not in raw


def test_the_stored_name_is_not_the_uploaded_one(member_client, member):
    upload(member_client, picture(), "../../etc/passwd.png")
    member.refresh_from_db()
    assert "/" not in member.avatar_path and ".." not in member.avatar_path
    assert "passwd" not in member.avatar_path


def test_a_new_picture_replaces_the_old_file(member_client, member, settings):
    upload(member_client, picture())
    first = member.__class__.objects.get(pk=member.pk).avatar_path
    upload(member_client, picture(size=(100, 100)))
    member.refresh_from_db()
    assert member.avatar_path != first
    assert stored(settings) == [member.avatar_path]


def test_a_file_that_is_not_a_picture_is_refused(member_client, member, settings):
    response = upload(member_client, b"just some text, honest", "me.png", "image/png")
    assert response.status_code == 200 and "picture" in response.content.decode().lower()
    member.refresh_from_db()
    assert member.avatar_path == "" and stored(settings) == []


@pytest.mark.parametrize(
    "content,name",
    [
        (b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "me.svg"),
        (b"GIF89a" + b"\x00" * 40, "me.gif"),
        (b"%PDF-1.4 hello", "me.png"),
    ],
)
def test_other_formats_are_refused_whatever_they_are_called(
    member_client, member, settings, content, name
):
    assert upload(member_client, content, name).status_code == 200
    assert stored(settings) == []


def test_a_huge_file_is_refused_before_it_is_read(member_client, member, settings):
    big = picture() + b"\x00" * (settings.AVATAR_MAX_BYTES + 1)
    assert upload(member_client, big).status_code == 200
    assert stored(settings) == []


def test_a_decompression_bomb_is_refused_without_a_crash(member_client, member, settings):
    # A valid PNG header that claims 60,000 x 60,000 pixels.
    def chunk(kind, data):
        import zlib

        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", 60000, 60000, 8, 2, 0, 0, 0)
    bomb = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")
    response = upload(member_client, bomb)
    assert response.status_code == 200
    assert stored(settings) == []


def test_removing_the_picture_deletes_the_file(member_client, member, settings):
    upload(member_client, picture())
    response = member_client.post(reverse("member:avatar_remove"))
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.avatar_path == "" and stored(settings) == []


def test_upload_needs_a_login_and_a_post(client, member_client):
    assert client.post(reverse("member:avatar")).status_code == 302
    assert member_client.get(reverse("member:avatar")).status_code == 405


def test_the_picture_is_served_to_members_with_safe_headers(member_client, other_client, member):
    upload(member_client, picture())
    member.refresh_from_db()
    url = reverse("member:avatar_file", args=[member.avatar_path])
    for client in (member_client, other_client):
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == "image/webp"
        assert response["X-Content-Type-Options"] == "nosniff"
        assert "private" in response["Cache-Control"]


def test_the_picture_is_not_served_to_the_signed_out(client, member_client, member):
    upload(member_client, picture())
    member.refresh_from_db()
    response = client.get(reverse("member:avatar_file", args=[member.avatar_path]))
    assert response.status_code == 302 and "/login/" in response["Location"]


@pytest.mark.parametrize("name", ["..%2F..%2Fetc%2Fpasswd", "a.png", "x" * 80 + ".webp", "..webp"])
def test_only_names_we_made_are_served(member_client, name):
    assert member_client.get(f"/avatars/{name}").status_code == 404


def test_the_picture_shows_in_the_header_and_on_the_profile(member_client, member):
    upload(member_client, picture())
    member.refresh_from_db()
    src = reverse("member:avatar_file", args=[member.avatar_path])
    assert src in member_client.get(reverse("accounts:me")).content.decode()


def test_without_a_picture_it_is_still_the_initial(member_client):
    html = member_client.get("/").content.decode()
    assert 'aria-label="Profile">M<' in html


def test_a_big_but_honest_picture_is_refused_on_its_pixel_count_alone(
    member_client, member, settings
):
    settings.AVATAR_MAX_PIXELS = 1_000_000
    assert upload(member_client, picture(size=(1500, 1000))).status_code == 200
    assert stored(settings) == []


@pytest.mark.parametrize("fmt", ["GIF", "BMP", "TIFF"])
def test_real_pictures_in_other_formats_are_refused(member_client, member, settings, fmt):
    assert upload(member_client, picture(fmt, size=(40, 40))).status_code == 200
    assert stored(settings) == []


def test_picking_a_stock_avatar_sets_the_marker(member, member_client):
    response = member_client.post(reverse("member:avatar_stock"), {"avatar": "ghost"})
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.avatar_path == "stock:ghost"
    settings_html = member_client.get(reverse("member:settings")).content.decode()
    assert reverse("member:stock_avatar", args=["ghost"]) in settings_html
    assert reverse("member:stock_avatar", args=["ghost"]) in member_client.get(
        reverse("accounts:me")
    ).content.decode()


def test_an_unknown_stock_avatar_is_refused(member, member_client):
    member_client.post(reverse("member:avatar_stock"), {"avatar": "nope"})
    member.refresh_from_db()
    assert member.avatar_path == ""


def test_the_stock_file_serves(member_client):
    assert member_client.get(reverse("member:stock_avatar", args=["ghost"])).status_code == 200
    assert member_client.get(reverse("member:stock_avatar", args=["nope"])).status_code == 404
