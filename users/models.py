from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone



class User(AbstractUser):
    Vendeur = models.BooleanField(default=False)
    Administrateur_du_site = models.BooleanField(default=False)
    telephone = models.CharField(max_length=15, blank=True)

# Create your models here.
