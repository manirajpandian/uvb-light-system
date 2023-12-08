from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Company

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created and instance.is_staff and instance.is_superuser:
        if not Profile.objects.filter(user=instance).exists():
            profile = Profile.objects.create(user=instance)
            profile.username = instance.username
            profile.role_id = '0'
            profile.save()
        if not Company.objects.filter(user=instance).exists():
            company = Company.objects.create(user=instance)
            company.company_name = 'UVB'
            company.company_address = 'UVB'
            company.save()
