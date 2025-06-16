from django.contrib.auth.models import User
from django.db import models
import secrets
import uuid

def generate_api_key():
    return secrets.token_hex(32)  # generates a 64-character hex string

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=100)
    project_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_name} - {self.user.username}"

class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    key = models.CharField(max_length=64, unique=True, default=generate_api_key)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')  # One API key per user per project

    def __str__(self):
        return f"{self.user.username} - {self.project.project_name} - {self.key}"

    def masked_key(self):
        visible = 4
        masked_part = '*' * max(len(self.key) - visible, 0)
        return self.key[:visible] + masked_part
