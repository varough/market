from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import F
from decimal import Decimal
from .models import Boutique, AbonnementFournisseur, Categorie, Produit, Commande, ArticleCommande, Paiement, Notification


User = get_user_model()

# --- Users ---
class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "vendeur", "is_site_admin"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    vendeur = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "vendeur"]

    def create(self, validated_data):
        vendeur = validated_data.pop("vendeur", False)
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        user.vendeur = vendeur
        user.save()
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
    fournisseur = UserPublicSerializer(read_only=True)
    class Meta:
        model = Produit
        fields = [
            "id", "boutique", "fournisseur", "categorie", "nom", "description",
            "prix", "stock", "image", "actif", "cree_a"
        ]

# --- Orders ---
class ArticleCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCommande
        fields = ["product", "quantity"]

class CommandeSerializerSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = Commande
        fields = ["id", "product", "product_name", "quantity", "prix"]

class CommandeSerializer(serializers.ModelSerializer):
    items = ArticleCommandeSerializer(many=True, write_only=True)
    items_detail = ArticleCommandeSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = Commande
        fields = ["id", "client", "statut", "total_price", "created_at", "items", "items_detail"]
        read_only_fields = ["client", "statut", "total_price", "created_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        user = self.context["request"].user
        order = Commande.objects.create(client=user, **validated_data)

        total = Decimal(0)
        for it in items:
            product = it["produit"]
            qty = it["quantity"]
            if qty <= 0:
                raise serializers.ValidationError("Quantité invalide.")
            if product.stock < qty:
                raise serializers.ValidationError(f"Stock insuffisant pour {product.nom}.")

            OrderItem.objects.create(order=order, produit=product, quantity=qty, price=product.price)
            total += Decimal(qty) * product.price

            
            product.stock = F('stock') - qty
            product.save(update_fields=["stock"])

        order.total_price = total
        order.save(update_fields=["total_price"])
        return order

# --- Payments ---
class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ["id", "commande", "methode", "statut", "created_at"]
        read_only_fields = ["statut", "created_at"]

# --- Notifications ---
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]
