from django.db import models
from django.contrib.auth.hashers import make_password, check_password #to create an encrypted secret_Key

class Service(models.TextChoices):
    S3 = 'S3'
    AZURE = 'Azure'
    GC = 'GC'
    CUSTOM = 'Custom'


class Credentials(models.Model):
    access_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    storage = models.CharField(max_length=10, choices=Service.choices)

#Storing the secret_key in the db as an encrypted value:

    def set_secret_key(self, raw_secret_key):
        """Hash and store the secret key"""
        self.secret_key = make_password(raw_secret_key)  # 🔐 Hashing secret key

    def check_secret_key(self, raw_secret_key):
        """Verify if the given secret key matches the stored hash"""
        return check_password(raw_secret_key, self.secret_key)

    def save(self, *args, **kwargs):
        """Ensure the secret_key is always hashed before saving"""
        if not self.secret_key.startswith('pbkdf2_sha256$'):
            self.set_secret_key(self.secret_key)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Credentials for {self.get_storage_display()}"
