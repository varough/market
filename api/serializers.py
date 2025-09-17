from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import ( Boutique, AbonnementFournisseur, Categorie, Produit,Commande, ArticleCommande, Paiement, Notification)


User = get_user_model()

class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )
        return user

# --- Shops / Subscriptions ---
class BoutiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Boutique
        fields = ["id", "nom", "description", "actif", "cree_a"]


class AbonnementFournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonnementFournisseur
        fields = ["id", "fournisseur", "boutique", "actif", "debut", "fin"]
        read_only_fields = ["fournisseur", "actif", "debut", "fin"]


# --- Catalog ---
class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = "__all__"


class ProduitSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Produit
        fields = [
            "id", "boutique", "fournisseur", "categorie", "nom", "description",
            "prix", "stock", "image", "actif", "cree_a"
        ]


# --- Orders ---
class ArticleCommandeSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source="produit.nom", read_only=True)

    class Meta:
        model = ArticleCommande
        fields = ["id", "produit", "produit_nom", "quantite", "prix_unitaire"]
        read_only_fields = ["prix_unitaire"]


class CommandeSerializer(serializers.ModelSerializer):
    items = ArticleCommandeSerializer(many=True, write_only=True)
    items_detail = ArticleCommandeSerializer(source="articles", many=True, read_only=True)

    class Meta:
        model = Commande
        fields = ["id", "client", "statut", "prix_total", "cree_a", "items", "items_detail"]
        read_only_fields = ["client", "statut", "prix_total", "cree_a"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        user = self.context["request"].user
        commande = Commande.objects.create(client=user, **validated_data)

        total = Decimal(0)
        for it in items:
            produit = it["produit"]
            qty = it["quantite"]

            if qty <= 0:
                raise serializers.ValidationError("Quantité invalide.")
            if produit.stock < qty:
                raise serializers.ValidationError(f"Stock insuffisant pour {produit.nom}.")

            ArticleCommande.objects.create(
                commande=commande,
                produit=produit,
                quantite=qty,
                prix_unitaire=produit.prix
            )
            total += Decimal(qty) * produit.prix

            produit.stock = F("stock") - qty
            produit.save(update_fields=["stock"])

        commande.prix_total = total
        commande.save(update_fields=["prix_total"])
        return commande


# --- Payments ---
class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ["id", "commande", "methode", "statut", "cree_a"]
        read_only_fields = ["statut", "cree_a"]


# --- Notifications ---
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "lu", "cree_a"]
