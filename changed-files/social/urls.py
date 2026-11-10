from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("people/", views.people, name="people"),
    path("notifications/", views.notifications, name="notifications"),
    path("u/<str:username>/", views.profile, name="profile"),
    path("u/<str:username>/library/", views.profile_library, name="profile_library"),
    path("u/<str:username>/posts/", views.profile_posts, name="profile_posts"),
    path("u/<str:username>/follow/", views.follow, name="follow"),
    path("u/<str:username>/unfollow/", views.unfollow, name="unfollow"),
    path("me/visibility/", views.visibility, name="visibility"),
    path("title/<int:pk>/post/", views.post_create, name="post_create"),
    path("post/<int:pk>/", views.post_detail, name="post"),
    path("post/<int:pk>/edit/", views.post_edit, name="post_edit"),
    path("post/<int:pk>/delete/", views.post_delete, name="post_delete"),
    path("post/<int:pk>/like/", views.like, name="like"),
    path("post/<int:pk>/comments/", views.comments, name="comments"),
    path("post/<int:pk>/comments/add/", views.comment_add, name="comment_add"),
    path("post/<int:pk>/spoiler/", views.spoiler, name="spoiler"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("comments/<int:pk>/spoiler/", views.comment_spoiler, name="comment_spoiler"),
]
