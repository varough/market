from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (BoutiqueViewSet, CategorieViewSet, ProduitViewSet, CommandeViewSet,register, login, me, vendeur , my_notifications, mark_notification_read
)

router = DefaultRouter()
router.register("boutiques", BoutiqueViewSet, basename="boutique")
router.register("categories", CategorieViewSet, basename="categorie")
router.register("produits", ProduitViewSet, basename="produit")
router.register("commandes", CommandeViewSet, basename="commande")

urlpatterns = [
                 
   path("", include(router.urls)),
   path("paiements/initiate/", vendeur),
   path("paiements/webhook/", vendeur),
   path("notifications/", my_notifications),
   path("notifications/<int:pk>/read/", mark_notification_read),
]
