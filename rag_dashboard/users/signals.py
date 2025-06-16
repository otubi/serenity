from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import APIKey

@receiver(post_save, sender=User)
def create_api_key(sender, instance, created, **kwargs):
    if created:
        APIKey.objects.create(user=instance)
