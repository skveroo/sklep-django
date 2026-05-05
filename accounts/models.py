from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='Kod pocztowy')
    city = models.CharField(max_length=100, blank=True, verbose_name='Miejscowość')
    street = models.CharField(max_length=200, blank=True, verbose_name='Ulica')
    house_number = models.CharField(max_length=20, blank=True, verbose_name='Numer domu')
    apartment_number = models.CharField(max_length=20, blank=True, verbose_name='Numer mieszkania')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')

    @property
    def full_address(self):
        parts = []
        if self.street:
            addr = f"ul. {self.street} {self.house_number}".strip()
            if self.apartment_number:
                addr += f"/{self.apartment_number}"
            parts.append(addr)
        if self.postal_code or self.city:
            parts.append(f"{self.postal_code} {self.city}".strip())
        return ", ".join(parts)

    def __str__(self):
        return f"Profil: {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
