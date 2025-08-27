from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    Vendeur = models.BooleanField(default=False)
    Administrateur_du_site = models.BooleanField(default=False)
    telephone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.username


class Boutique(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="boutiques"
    )
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    cree_a = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom



class AbonnementFournisseur(models.Model):
    fournisseur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="abonnements"
    )
    boutique = models.ForeignKey(Boutique, on_delete=models.CASCADE, related_name="abonnements")
    actif = models.BooleanField(default=True)
    debut = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.fournisseur} → {self.boutique}"


class Categorie(models.Model):
    nom = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.nom


class Produit(models.Model):
    boutique = models.ForeignKey(Boutique, on_delete=models.CASCADE, related_name="produits")
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, related_name="produits")
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    cree_a = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Commande(models.Model):
    STATUTS = [
        ("en_attente", "En attente"),
        ("paye", "Payé"),
        ("expedie", "Expédié"),
        ("annule", "Annulé"),
    ]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="commandes")
    statut = models.CharField(max_length=20, choices=STATUTS, default="en_attente")
    prix_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cree_a = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande {self.id} - {self.client}"


class ArticleCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="articles")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"


class Paiement(models.Model):
    STATUS = [
        ("en_attente", "En attente"),
        ("termine", "Terminé"),
        ("echoue", "Échoué"),
    ]
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="paiements")
    methode = models.CharField(max_length=50, default="stripe")
    statut = models.CharField(max_length=20, choices=STATUS, default="en_attente")
    cree_a = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.id} - {self.statut}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField(max_length=255)
    lu = models.BooleanField(default=False)
    cree_a = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.utilisateur}] {self.message}"
