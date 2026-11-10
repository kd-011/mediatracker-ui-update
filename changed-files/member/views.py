from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import FileResponse, Http404, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from accounts import throttle
from accounts.models import User
from . import export as exports
from . import services
from .forms import AvatarForm, DeleteForm, PasswordForm, PreferencesForm, ProfileForm

LOCKED = "Too many wrong passwords. Wait about {minutes} minutes and try again."


def _locked(request, template, context):
    minutes = settings.THROTTLE_WINDOW_SECONDS // 60
    return render(
        request, template, {**context, "locked": LOCKED.format(minutes=minutes)}, status=429
    )


def _settings_context(request, **forms):
    user = request.user
    return {
        "preferences_form": PreferencesForm(
            initial={
                "title_language": user.title_language,
                "show_adult": user.show_adult,
                "default_visibility": user.default_visibility,
            }
        ),
        "password_form": PasswordForm(user=user),
        "avatar_form": AvatarForm(),
        "profile_form": ProfileForm(instance=user),
        "stock_avatars": services.STOCK_AVATARS,
        "exports": [
            ("library.csv", "Library", "CSV"),
            ("diary.csv", "Diary", "CSV"),
            ("episodes.csv", "Episode scores and comments", "CSV"),
            ("anime.xml", "Anime list", "MyAnimeList XML"),
            ("manga.xml", "Manga list", "MyAnimeList XML"),
        ],
        **forms,
    }


def settings_screen(request):
    return render(request, "member/settings.html", _settings_context(request))


@require_POST
def preferences(request):
    form = PreferencesForm(request.POST)
    if not form.is_valid():
        return render(
            request, "member/settings.html", _settings_context(request, preferences_form=form)
        )
    user = request.user
    user.title_language = form.cleaned_data["title_language"]
    user.show_adult = form.cleaned_data["show_adult"]
    user.default_visibility = form.cleaned_data["default_visibility"]
    user.save(update_fields=["title_language", "show_adult", "default_visibility", "updated_at"])
    messages.success(request, "Saved.")
    return redirect("member:settings")


@require_POST
def password(request):
    user = request.user
    key = str(user.pk)
    context = _settings_context(request)
    if throttle.is_locked("password-user", key, settings.LOGIN_MAX_FAILURES):
        return _locked(request, "member/settings.html", context)
    form = PasswordForm(request.POST, user=user)
    if form.is_valid():
        if not user.check_password(form.cleaned_data["current"]):
            throttle.record_failure("password-user", key)
            form.add_error("current", "That isn't your current password.")
        else:
            throttle.clear("password-user", key)
            services.change_password(user, form.cleaned_data["new"])
            # Every session ended, this one too: this device signs straight back in.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Password changed. Other devices were signed out.")
            return redirect("member:settings")
    return render(request, "member/settings.html", _settings_context(request, password_form=form))


@require_POST
def profile(request):
    form = ProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("member:settings")
    return render(request, "member/settings.html", _settings_context(request, profile_form=form))


@require_POST
def avatar(request):
    form = AvatarForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            services.set_avatar(request.user, form.cleaned_data["file"])
        except services.AvatarError as exc:
            form.add_error("file", str(exc))
        else:
            messages.success(request, "Picture updated.")
            return redirect("member:settings")
    return render(request, "member/settings.html", _settings_context(request, avatar_form=form))


@require_POST
def avatar_remove(request):
    services.remove_avatar(request.user)
    messages.success(request, "Picture removed.")
    return redirect("member:settings")


@require_POST
def avatar_stock(request):
    try:
        services.set_stock_avatar(request.user, request.POST.get("avatar", ""))
    except services.AvatarError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Picture updated.")
    return redirect("member:settings")


@require_GET
def stock_avatar(request, key):
    path = services.stock_avatar_file(key)
    if path is None:
        raise Http404
    return FileResponse(path.open("rb"), content_type="image/svg+xml")


@require_GET
def avatar_file(request, name):
    path = services.avatar_path(name)
    if path is None or not path.is_file():
        raise Http404
    response = FileResponse(path.open("rb"), content_type="image/webp")
    # The name changes whenever the picture does, so it can be kept for good, by this browser only.
    response["Cache-Control"] = "private, max-age=31536000, immutable"
    return response


@require_GET
def export(request, kind):
    if kind not in exports.FILES:
        raise Http404
    content_type, make = exports.FILES[kind]
    response = StreamingHttpResponse(make(request.user), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="mediatracker-{kind}"'
    response["Cache-Control"] = "private, no-store"
    return response


def delete(request):
    user = User.objects.get(pk=request.user.pk)
    if request.method != "POST":
        return render(request, "member/delete.html", {"form": DeleteForm()})
    key = str(user.pk)
    form = DeleteForm(request.POST)
    if throttle.is_locked("delete-user", key, settings.LOGIN_MAX_FAILURES):
        return _locked(request, "member/delete.html", {"form": form})
    if form.is_valid():
        if not user.check_password(form.cleaned_data["password"]):
            throttle.record_failure("delete-user", key)
            form.add_error("password", "That isn't your password.")
        elif form.cleaned_data["confirm"].strip().lower() != user.username.lower():
            form.add_error("confirm", f"Type {user.username} exactly, to be sure.")
        else:
            try:
                services.delete_account(user)
            except services.CannotLeave as exc:
                form.add_error(None, str(exc))
            else:
                throttle.clear("delete-user", key)
                logout(request)
                messages.success(request, "Your account and everything in it is deleted.")
                return redirect("accounts:login")
    return render(request, "member/delete.html", {"form": form})
