from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "Vendeur", "Administrateur_du_site", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Rôles", {"fields": ("Vendeur", "Administrateur_du_site","telephone")}),)

# Register your models here.
