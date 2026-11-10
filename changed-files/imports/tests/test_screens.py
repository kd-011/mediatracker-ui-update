"""The import screens: idle, running, done and review, who can see them, and what they refuse."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Media
from imports.models import ImportJob, ImportRow

from .conftest import STANDARD, import_mal, mal_gz, upload

pytestmark = pytest.mark.django_db

HOME = "imports:index"


def page(client, name=HOME, *args, **kwargs):
    return client.get(reverse(name, args=args), **kwargs)


def job_for(user, source="mal_xml", status="running", total=10, **extra):
    return ImportJob.objects.create(
        user=user, source=source, status=status, total_rows=total, **extra
    )


def rows_for(job, count, kind="added", **extra):
    """`kind` is an outcome (added, already_there) or a status (failed, skipped)."""
    fields = (
        {"status": "auto", "outcome": kind}
        if kind in ("added", "already_there")
        else {"status": kind}
    )
    ImportRow.objects.bulk_create(
        [
            ImportRow(
                job=job,
                position=job.rows.count() + i,
                raw_data={"name": f"Film {i}"},
                **fields,
                **extra,
            )
            for i in range(count)
        ]
    )


# ---- Who can get in ----


def test_every_import_url_needs_a_login(member):
    job = job_for(member)
    row = ImportRow.objects.create(job=job, position=0, status="needs_review", raw_data={})
    anonymous = Client()
    for name, args in (
        (HOME, []),
        ("imports:job", [job.pk]),
        ("imports:review", [job.pk]),
    ):
        response = anonymous.get(reverse(name, args=args))
        assert response.status_code == 302 and "/login/" in response["Location"], name
    for name, args in (
        ("imports:upload_mal", []),
        ("imports:upload_letterboxd", []),
        ("imports:confirm_row", [row.pk]),
        ("imports:skip_row", [row.pk]),
        ("imports:retry", [job.pk]),
    ):
        response = anonymous.post(reverse(name, args=args))
        assert response.status_code == 302 and "/login/" in response["Location"], name


def test_uploads_need_the_csrf_token(member):
    client = Client(enforce_csrf_checks=True)
    client.force_login(member)
    response = upload(client, "animelist.xml.gz", mal_gz(*STANDARD))
    assert response.status_code == 403
    assert ImportJob.objects.count() == 0


def test_someone_elses_job_is_a_404_on_every_screen(member, other):
    job = job_for(other)
    stranger = Client()
    stranger.force_login(member)
    assert page(stranger, "imports:job", job.pk).status_code == 404
    assert page(stranger, "imports:review", job.pk).status_code == 404
    assert stranger.post(reverse("imports:retry", args=[job.pk])).status_code == 404


def test_the_settings_page_links_to_the_import_screen(member_client):
    response = page(member_client, "member:settings")
    assert reverse(HOME) in response.content.decode()


# ---- Idle ----


def test_idle_has_both_sources_with_their_own_words(member_client):
    html = page(member_client).content.decode()
    assert "MyAnimeList XML" in html
    assert "Titles match exactly by MAL ID." in html
    assert "Letterboxd zip" in html
    assert (
        "Exact title and year matches are added automatically. The rest come here for review."
        in html
    )
    assert "Imports never create posts, and importing again only adds what" in html
    assert 'type="file"' in html
    assert "no points" in html.lower() or "earn no" in html.lower()


def test_idle_does_not_poll(member_client):
    assert "every 2s" not in page(member_client).content.decode()


def test_idle_says_what_the_limits_are(member_client, settings):
    html = page(member_client).content.decode()
    assert f"{settings.IMPORT_MAX_UPLOAD_BYTES // (1024 * 1024)} MB" in html


def test_without_a_tmdb_key_the_letterboxd_form_says_why_it_is_off(member_client, settings):
    settings.TMDB_API_KEY = ""
    html = page(member_client).content.decode()
    assert "TMDB is off" in html
    assert 'name="file"' in html  # still there for MAL
    assert html.count('type="file"') == 1


def test_with_a_key_both_forms_are_there(member_client, tmdb_key):
    assert page(member_client).content.decode().count('type="file"') == 2


# ---- Running ----


def test_a_running_job_shows_live_progress_and_polls(member, member_client):
    job = job_for(member, total=10)
    rows_for(job, 4)
    html = page(member_client).content.decode()
    assert 'role="progressbar"' in html
    assert 'aria-valuenow="40"' in html
    assert "4 of 10" in html
    assert f'hx-get="{reverse("imports:job", args=[job.pk])}' in html
    assert "every 2s" in html


def test_a_queued_job_says_it_is_waiting_for_the_worker(member, member_client):
    job_for(member, status="queued", total=0)
    html = page(member_client).content.decode()
    assert "Waiting" in html


def test_the_poll_answers_204_when_nothing_changed(member, member_client):
    job = job_for(member)
    rows_for(job, 2)
    first = page(member_client, "imports:job", job.pk)
    assert first.status_code == 200
    version = first.headers["X-Version"]
    unchanged = member_client.get(reverse("imports:job", args=[job.pk]) + f"?v={version}")
    assert unchanged.status_code == 204
    rows_for(job, 1)
    changed = member_client.get(reverse("imports:job", args=[job.pk]) + f"?v={version}")
    assert changed.status_code == 200


def test_mal_details_show_honest_progress_after_the_rows_are_ready(member, member_client):
    job = job_for(member, status="done", total=3, finished_at=timezone.now())
    for i, pending in enumerate((False, True, True)):
        media = Media.objects.create(
            type="anime", title=f"T{i}", metadata_source="mal", details_pending=pending
        )
        ImportRow.objects.create(
            job=job, position=i, status="auto", outcome="added", raw_data={}, resolved_media=media
        )
    html = page(member_client).content.decode()
    assert "Your library rows are ready" in html
    assert "1 of 3" in html
    assert "minute" in html  # an honest upper bound, not a promise
    assert "every 2s" in html  # still polling while details come in


def test_the_page_stops_polling_when_the_details_are_in(member, member_client):
    job = job_for(member, status="done", total=1, finished_at=timezone.now())
    media = Media.objects.create(
        type="anime", title="T", metadata_source="mal", details_pending=False
    )
    ImportRow.objects.create(
        job=job, position=0, status="auto", outcome="added", raw_data={}, resolved_media=media
    )
    assert "every 2s" not in page(member_client).content.decode()


# ---- Done ----


def test_done_shows_the_counts(member, member_client):
    job = job_for(member, status="done", total=7, finished_at=timezone.now())
    rows_for(job, 4, "added")
    rows_for(job, 2, "already_there")
    rows_for(job, 1, "failed", error="Unknown status 'Mystery'.")
    html = page(member_client).content.decode()
    assert "4 added" in html
    assert "2 already in your library" in html
    assert "1 failed" in html
    assert "Unknown status" in html
    assert reverse("core:library") in html


def test_a_failed_job_says_why_in_words(member, member_client):
    job_for(member, status="failed", total=0, error="That is not a valid MyAnimeList export.")
    html = page(member_client).content.decode()
    assert "That is not a valid MyAnimeList export." in html
    assert 'type="file"' in html  # and the form is back for another try


# ---- Review ----


def test_the_review_screen_lists_rows_with_candidate_chips_and_two_actions(member, member_client):
    job = job_for(member, source="letterboxd_zip", status="review", total=2)
    ImportRow.objects.create(
        job=job,
        position=0,
        status="needs_review",
        confidence=0.7,
        raw_data={"name": "Oldish Film", "year": 2004, "score": 9},
        candidates=[
            {
                "source": "tmdb",
                "namespace": "movie",
                "external_id": "1",
                "title": "Oldish Film",
                "year": 2003,
            },
            {
                "source": "tmdb",
                "namespace": "movie",
                "external_id": "2",
                "title": "Oldish Film",
                "year": 2013,
            },
        ],
    )
    html = page(member_client, "imports:review", job.pk).content.decode()
    assert "Oldish Film, 2004" in html
    assert "Oldish Film (2003)" in html and "Oldish Film (2013)" in html
    assert html.count('type="radio"') == 2
    assert "Confirm" in html and "Skip" in html
    assert "1 to review" in html


def test_a_row_with_no_candidates_can_only_be_skipped(member, member_client):
    job = job_for(member, source="letterboxd_zip", status="review", total=1)
    ImportRow.objects.create(
        job=job,
        position=0,
        status="needs_review",
        raw_data={"name": "Lost", "year": 1999},
        candidates=[],
    )
    html = page(member_client, "imports:review", job.pk).content.decode()
    assert "No match found" in html
    assert "Confirm" not in html
    assert "Skip" in html


def test_review_is_paged(member, member_client):
    job = job_for(member, source="letterboxd_zip", status="review", total=60)
    for i in range(60):
        ImportRow.objects.create(
            job=job,
            position=i,
            status="needs_review",
            raw_data={"name": f"Film {i}", "year": 2000},
            candidates=[],
        )
    html = page(member_client, "imports:review", job.pk).content.decode()
    assert "60 to review" in html
    assert html.count("Film ") < 60
    assert "?after=" in html or "after=" in html


def test_the_review_screen_names_the_finished_state(member, member_client):
    job = job_for(
        member, source="letterboxd_zip", status="done", total=1, finished_at=timezone.now()
    )
    html = page(member_client, "imports:review", job.pk).content.decode()
    assert "Review finished." in html


def test_titles_with_markup_are_escaped_on_the_review_screen(member, member_client):
    job = job_for(member, source="letterboxd_zip", status="review", total=1)
    ImportRow.objects.create(
        job=job,
        position=0,
        status="needs_review",
        raw_data={"name": "<script>alert(1)</script>", "year": 2000},
        candidates=[
            {
                "source": "tmdb",
                "namespace": "movie",
                "external_id": "1",
                "title": "<b>x</b>",
                "year": 2000,
            }
        ],
    )
    html = page(member_client, "imports:review", job.pk).content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "<b>x</b>" not in html


# ---- Upload checks ----


def test_a_file_over_the_limit_is_refused_before_it_is_kept(member_client, settings):
    settings.IMPORT_MAX_UPLOAD_BYTES = 1000
    response = upload(member_client, "animelist.xml.gz", b"x" * 5000)
    assert response.status_code == 413
    assert "MB" in response.content.decode() or "too large" in response.content.decode()
    assert ImportJob.objects.count() == 0
    assert (
        not settings.IMPORT_UPLOAD_DIR.exists() or list(settings.IMPORT_UPLOAD_DIR.iterdir()) == []
    )


def test_a_declared_length_over_the_limit_is_refused_without_reading_the_body(
    member_client, settings
):
    settings.IMPORT_MAX_UPLOAD_BYTES = 1000
    response = member_client.post(
        reverse("imports:upload_mal"),
        data=b"x",
        content_type="multipart/form-data; boundary=x",
        headers={"content-length": "999999999"},
    )
    assert response.status_code == 413


def test_no_file_is_a_clear_error(member_client):
    response = member_client.post(reverse("imports:upload_mal"), {})
    assert response.status_code == 400
    assert "Choose a file" in response.content.decode()


def test_a_file_that_is_not_the_right_kind_is_refused_by_its_first_bytes(member_client):
    response = upload(member_client, "animelist.xml.gz", b"MZ\x90\x00 definitely a program")
    assert response.status_code == 400
    assert ImportJob.objects.count() == 0
    response = upload(
        member_client, "x.zip", b"hello", "imports:upload_letterboxd", "application/zip"
    )
    assert response.status_code == 400


def test_the_upload_name_never_reaches_the_disk(member_client, settings):
    import_mal(member_client, mal_gz(*STANDARD), name="../../etc/passwd.xml.gz")
    [kept] = settings.IMPORT_UPLOAD_DIR.iterdir()
    assert "passwd" not in kept.name and ".." not in kept.name
    assert kept.parent == settings.IMPORT_UPLOAD_DIR


def test_get_on_an_upload_url_is_not_allowed(member_client):
    assert member_client.get(reverse("imports:upload_mal")).status_code == 405
    assert member_client.get(reverse("imports:upload_letterboxd")).status_code == 405


def test_the_old_jobs_are_listed_newest_first_and_capped(member, member_client):
    for i in range(8):
        job_for(member, status="done", total=1, finished_at=timezone.now() - timedelta(days=i))
    html = page(member_client).content.decode()
    assert html.count('class="import-job') <= 6 + 2


def test_a_poll_that_finds_the_job_settled_asks_the_page_to_reload(member, member_client):
    job = job_for(member, status="done", total=1, finished_at=timezone.now())
    rows_for(job, 1)
    response = member_client.get(reverse("imports:job", args=[job.pk]) + "?v=stale")
    assert response.status_code == 200
    assert response.headers["HX-Refresh"] == "true"


def test_a_poll_of_a_job_still_going_does_not_reload_the_page(member, member_client):
    job = job_for(member)
    response = member_client.get(reverse("imports:job", args=[job.pk]) + "?v=stale")
    assert "HX-Refresh" not in response.headers


def test_the_import_page_does_not_say_it_is_the_home_tab(member_client):
    html = page(member_client).content.decode()
    assert 'aria-current="page"' not in html


def test_the_home_page_still_marks_its_own_tab(member_client):
    assert 'aria-current="page"' in member_client.get("/").content.decode()
