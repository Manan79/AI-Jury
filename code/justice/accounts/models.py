from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_token_expired(self):
        expiration_days = 7  # Token valid for 7 days
        return (timezone.now() - self.created_at).days > expiration_days

    def __str__(self):
        return f"{self.user.username} - {'Verified' if self.is_verified else 'Pending'}"