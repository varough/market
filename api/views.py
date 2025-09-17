from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import UserPublicSerializer
from .models import Boutique, AbonnementFournisseur, Categorie, Produit, Commande, Paiement, Notification
from .serializers import (RegisterSerializer, CategorieSerializer, BoutiqueSerializer, ProduitSerializer,CommandeSerializer, PaiementSerializer, NotificationSerializer)
from .permissions import IsSiteAdmin, vendeur

User = get_user_model()

# ---------------- AUTH ----------------
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserPublicSerializer(user).data},
                        status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserPublicSerializer(user).data})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(UserPublicSerializer(request.user).data)

# ---------------- BOUTIQUE ----------------
class BoutiqueViewSet(viewsets.ModelViewSet):
    queryset = Boutique.objects.all()
    serializer_class = BoutiqueSerializer

    @action(detail=True, methods=["post"], permission_classes=[vendeur])
    def subscribe(self, request, pk=None):
        boutique = self.get_object()
        sub, created = AbonnementFournisseur.objects.get_or_create(
            fournisseur=request.user, boutique=boutique
        )
        sub.actif = True
        sub.fin = None
        sub.save()
        return Response({"detail": "Abonnement activé.", "created": created})

    @action(detail=True, methods=["post"], permission_classes=[vendeur])
    def unsubscribe(self, request, pk=None):
        boutique = self.get_object()
        try:
            sub = AbonnementFournisseur.objects.get(
                fournisseur=request.user, boutique=boutique, actif=True
            )
            sub.actif = False
            sub.fin = timezone.now()
            sub.save()
            return Response({"detail": "Abonnement désactivé."})
        except AbonnementFournisseur.DoesNotExist:
            return Response({"detail": "Pas d'abonnement actif"}, status=status.HTTP_400_BAD_REQUEST)

class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all().order_by("nom")
    serializer_class = CategorieSerializer

# ---------------- PRODUITS ----------------
class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.filter(actif=True).select_related("boutique", "categorie")
    serializer_class = ProduitSerializer
    filterset_fields = ["boutique", "categorie"]
    search_fields = ["nom", "description"]
    ordering_fields = ["prix", "cree_a"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [vendeur()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        boutique = serializer.validated_data.get("boutique")
        has_sub = AbonnementFournisseur.objects.filter(
            fournisseur=self.request.user, boutique=boutique, actif=True
        ).exists()
        if not has_sub:
            raise permissions.PermissionDenied("Vous devez être abonné à cette boutique.")
        serializer.save()

# ---------------- COMMANDES ----------------
class CommandeViewSet(viewsets.ModelViewSet):
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Commande.objects.filter(client=self.request.user).order_by("-cree_a")

    def perform_create(self, serializer):
        commande = serializer.save(client=self.request.user)
        Notification.objects.create(
            user=self.request.user,
            message=f"Votre commande {commande.id} a été créée avec succès."
        )

# ---------------- PAIEMENTS ----------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    serializer = PaiementSerializer(data=request.data)
    if serializer.is_valid():
        payment = serializer.save(statut="en_attente")
        Notification.objects.create(
            user=payment.commande.client,
            message=f"Votre paiement pour la commande {payment.commande.id} a été initié."
        )
        return Response(PaiementSerializer(payment).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def payment_webhook(request):
    event = request.data.get("event")
    data = request.data.get("data", {})

    if event == "payment.succeeded":
        commande_id = data.get("commande_id")
        try:
            payment = Paiement.objects.get(commande_id=commande_id)
            payment.statut = "termine"
            payment.save(update_fields=["statut"])
            Notification.objects.create(
                user=payment.commande.client,
                message=f"Votre paiement pour la commande {payment.commande.id} a été confirmé."
            )
            return Response({"status": "success"})
        except Paiement.DoesNotExist:
            return Response({"detail": "commande non trouvée"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"status": "ignored"})

# ---------------- NOTIFICATIONS ----------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by("-cree_a")
    return Response(NotificationSerializer(notifs, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        notif = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"detail": "notification non trouvée"}, status=status.HTTP_404_NOT_FOUND)

    notif.lu = True
    notif.save(update_fields=["lu"])
    return Response({"detail": "ok"})
