from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import  Boutique, AbonnementFournisseur, Categorie, Produit, Commande, ArticleCommande, Paiement, Notification




@admin.register(Boutique)
class BoutiqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "description", "actif", "cree_a")
    search_fields = ("nom", )
    list_filter = ("actif", )


@admin.register(AbonnementFournisseur)
class AbonnementFournisseurAdmin(admin.ModelAdmin):
    list_display = ("fournisseur", "boutique", "actif", "debut", "fin")
    list_filter = ("actif", )
    search_fields = ("fournisseur__username", "boutique__nom")


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug")
    prepopulated_fields = {"slug": ("nom", )}


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ("boutique", "categorie", "nom", "prix", "stock", "actif", "cree_a", "short_description")
    search_fields = ("nom", "description")

    def short_description(self, obj):
        return obj.description[:50] + "..." if obj.description else ""
    short_description.short_description = "Description"


class ArticleCommandeInline(admin.TabularInline):
    model = ArticleCommande
    extra = 1


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("client", "prix_total", "statut", "cree_a")
    list_filter = ("statut", )
    search_fields = ("client__username", )
    inlines = [ArticleCommandeInline]


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("commande", "methode", "statut", "cree_a")
    list_filter = ("methode", "statut")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "short_message", "lu", "cree_a")
    list_filter = ("lu", )

    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message"
