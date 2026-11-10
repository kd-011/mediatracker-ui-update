from django.urls import path, re_path

from . import views

app_name = "member"

urlpatterns = [
    path("settings/", views.settings_screen, name="settings"),
    path("settings/preferences/", views.preferences, name="preferences"),
    path("settings/password/", views.password, name="password"),
    path("settings/profile/", views.profile, name="profile"),
    path("settings/avatar/", views.avatar, name="avatar"),
    path("settings/avatar/remove/", views.avatar_remove, name="avatar_remove"),
    path("settings/avatar/stock/", views.avatar_stock, name="avatar_stock"),
    re_path(r"^avatars/stock/(?P<key>[a-z]{1,20})\.svg$", views.stock_avatar, name="stock_avatar"),
    path("settings/export/<str:kind>", views.export, name="export"),
    path("settings/delete/", views.delete, name="delete"),
    re_path(
        r"^avatars/(?P<name>[A-Za-z0-9_-]{1,64}\.webp)$", views.avatar_file, name="avatar_file"
    ),
]
