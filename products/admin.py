from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Boutique,  AbonnementFournisseur, Categorie, Produit, Commande, ArticleCommande, Paiement, Notification

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "Vendeur", "Administrateur_du_site", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Rôles", {"fields": ("Vendeur", "Administrateur_du_site","telephone")}),)

@admin.register(Boutique)
class BoutiqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "description", "actif", "cree_a")
    search_fields = ("nom", )

@admin.register(AbonnementFournisseur)
class AbonnementFournisseurAdmin(admin.ModelAdmin):
    list_display = ("boutique", "actif", "debut", "fin")
    list_filter= ("actif" ,)

# Register your models here.
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug")
    prepopulated_fields = {"slug": ("nom", )}

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("boutique", "categorie", "nom", "prix", "stock", "actif", "cree_a", "description")
    search_fields = ("nom", "description")


class ArticleCommandeInline(admin.TabularInline):
    model = ArticleCommande
    extra = 1

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("client", "prix_total", "statut", "cree_a")
    list_filter = ("statut", )
    inlines = [ArticleCommandeInline]

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("commande", "methode", "statut", "cree_a")
    list_filter = ("methode", "statut")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "lu", "cree_a")
    list_filter = ("lu", )
