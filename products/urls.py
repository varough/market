from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()
router.register("boutiques", BoutiqueViewSet, basename="boutique")
router.register("categories", CategorieViewSet, basename="categorie")
router.register("produits", ProduitViewSet, basename="produit")
router.register("commandes", CommandeViewSet, basename="commande")

urlpatterns = [
   path("auth/register/", register),
   path("auth/login", login),
   path("auth/me", me),
   path("", include(router.urls)),
   path("paiements/initiate/", vendeur),
   path("paiements/webhook/", vendeur),
   path("notifications/", my_notifications),
   path("notifications/<int:pk>/read/", mark_notification_read),
]
