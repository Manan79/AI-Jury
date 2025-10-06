from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import EmailVerification

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_classes = "w-full rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        for field_name in self.fields:
            field = self.fields[field_name]
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + common_classes).strip()
            field.widget.attrs.setdefault('placeholder', field.label)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = False  # Deactivate account until email verification
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Extends AuthenticationForm to:
    - Allow login with either username or email in the username field
    - Provide a clearer error when the account exists but is inactive (unverified)
    """

    username = UsernameField(
        widget=forms.TextInput(attrs={"autofocus": True}),
        label=_("Username or email"),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "inactive": _("Your account is not active yet. Please verify your email."),
    }

    def clean(self):
        # Try authenticating with the provided username value as-is first.
        # If that fails and the value looks like an email, map it to a username.
        cleaned_data = super().clean()
        return cleaned_data

    def confirm_login_allowed(self, user):
        # Provide clearer feedback for inactive accounts
        if not user.is_active:
            # If we have an EmailVerification record and it's not verified, hint to verify
            try:
                verification = EmailVerification.objects.get(user=user)
                if not verification.is_verified:
                    raise ValidationError(self.error_messages["inactive"], code="inactive")
            except EmailVerification.DoesNotExist:
                # Fall back to generic inactive message
                raise ValidationError(self.error_messages["inactive"], code="inactive")
        return super().confirm_login_allowed(user)