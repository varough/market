from django.contrib.auth import get_user_model
from django.db.models import F
from rest_framework import serializers

User = get_user_model()

# --- Users ---
class UserSerializer(serializers.ModelSerializer):
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