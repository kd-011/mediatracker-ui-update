from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from accounts.models import User


def _password(autocomplete, label):
    return forms.CharField(
        label=label,
        max_length=256,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": autocomplete}, render_value=False),
    )


class PreferencesForm(forms.Form):
    title_language = forms.ChoiceField(label="Title language", choices=User.TitleLanguage.choices)
    show_adult = forms.BooleanField(label="Show adult titles", required=False)
    default_visibility = forms.ChoiceField(
        label="Default visibility", choices=User.Visibility.choices
    )


class PasswordForm(forms.Form):
    current = _password("current-password", "Current password")
    new = _password("new-password", "New password")
    again = _password("new-password", "New password again")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        new, again = cleaned.get("new"), cleaned.get("again")
        if new and again and new != again:
            self.add_error("again", "The two passwords do not match.")
        elif new:
            try:
                validate_password(new, self.user)
            except ValidationError as exc:
                self.add_error("new", exc)
        return cleaned


class DeleteForm(forms.Form):
    password = _password("current-password", "Your password")
    confirm = forms.CharField(
        label="Type your username to confirm",
        max_length=150,
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "autocapitalize": "none", "spellcheck": "false"}
        ),
    )


class AvatarForm(forms.Form):
    file = forms.FileField(label="Picture")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["display_name", "username"]
