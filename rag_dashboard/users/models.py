from django.contrib.auth.models import User
from django.db import models
import secrets

def generate_api_key():
    return secrets.token_hex(32)  # generates a 64-character hex string

class APIKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=64, unique=True, default=generate_api_key)

    def __str__(self):
        return f"{self.user.username} - {self.key}"
