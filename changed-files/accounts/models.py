from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError("A username is required")
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        return self.create_user(username, password, is_admin=True, **extra)

    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)


class User(AbstractBaseUser):
    class Visibility(models.TextChoices):
        MEMBERS = "members", "Members"
        PRIVATE = "private", "Private"

    class TitleLanguage(models.TextChoices):
        ENGLISH = "english", "English"
        ROMAJI = "romaji", "Romaji"
        NATIVE = "native", "Native"

    username = models.CharField(max_length=30, unique=True, validators=[UnicodeUsernameValidator()])
    display_name = models.CharField(max_length=60, blank=True)
    avatar_path = models.CharField(max_length=255, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    default_visibility = models.CharField(
        max_length=10, choices=Visibility.choices, default=Visibility.MEMBERS
    )
    title_language = models.CharField(
        max_length=10, choices=TitleLanguage.choices, default=TitleLanguage.ENGLISH
    )
    show_adult = models.BooleanField(default=False)
    # One of chud.rules.BUDDIES, or blank. Counts only while their level still reaches it.
    chud_buddy = models.CharField(max_length=20, blank=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("username"), name="user_username_ci_unique"),
        ]
        ordering = ["username"]

    def __str__(self):
        return self.username

    @property
    def name(self):
        return self.display_name or self.username

    @property
    def initial(self):
        return self.name[:1].upper()

    @property
    def avatar_url(self):
        from django.urls import reverse

        if not self.avatar_path:
            return ""
        if self.avatar_path.startswith("stock:"):
            return reverse("member:stock_avatar", args=[self.avatar_path.removeprefix("stock:")])
        return reverse("member:avatar_file", args=[self.avatar_path])

    # Django's admin site asks these questions of the user. In this app an admin is a
    # staff member and has every permission, and nobody else gets into /admin/.
    @property
    def is_staff(self):
        return self.is_active and self.is_admin

    @property
    def is_superuser(self):
        return self.is_active and self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Invite(models.Model):
    class Kind(models.TextChoices):
        SIGNUP = "signup", "Signup"
        PASSWORD_RESET = "password_reset", "Password reset"

    code = models.CharField(max_length=16, primary_key=True)
    kind = models.CharField(max_length=14, choices=Kind.choices)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invites_created")
    target_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="reset_codes"
    )
    used_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="invites_used"
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind="signup", target_user__isnull=True)
                | models.Q(kind="password_reset", target_user__isnull=False),
                name="invite_reset_has_target_user",
            ),
        ]

    def __str__(self):
        return f"{self.kind} {self.code}"

    @property
    def status(self):
        if self.used_at:
            return "used"
        if self.revoked_at:
            return "revoked"
        if self.expires_at <= timezone.now():
            return "expired"
        return "active"

    @property
    def is_usable(self):
        return self.status == "active"


class ThrottleHit(models.Model):
    """One failed attempt. Lives in Postgres so every gunicorn worker sees the same count."""

    scope = models.CharField(max_length=20)
    key = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["scope", "key", "created_at"])]

    def __str__(self):
        return f"{self.scope}:{self.key}"
