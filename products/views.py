from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import viewsets, status, permissions 
from rest_framework.decorators import api_view, permission_classes, action 
from rest_framework.response import Response
from rest_framework.authtoken.models import Token 
from .models import Boutique,AbonnementFournisseur,Categorie,Produit,Commande,ArticleCommande,Paiement,Notification
from .serializers import RegisterSerializer,UserPublicSerializer,BoutiqueSerializer, ProduitSerializer,CommandeSerializer,ArticleCommandeSerializer,PaiementSerializer,NotificationSerializer 
from .permissions import IsSiteAdmin , Est_ce_que_le_vendeur

User = get_user_model()
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Token, _ = Token.objects.get_or_create(user=user)
        return Response({"Token": Token.key, "user": UserPublicSerializer(user).data},
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

    Token, _ = Token.objects.get_or_create(user=user)
    return Response({"Token": Token.key, "user": UserPublicSerializer(user).data})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(UserPublicSerializer(request.user).data)

class BoutiqueViewSet(viewsets.ModelViewSet):
    queryset = Boutique.objects.all()
    serializer_class = BoutiqueSerializer

    # --- S'abonner ---
    @action(detail=True, methods=["post"], permission_classes=[Est_ce_que_le_vendeur])
    def subscribe(self, request, pk=None):
        boutique = self.get_object()
        sub, created = AbonnementFournisseur.objects.get_or_create(
            fournisseur=request.user, boutique=boutique
        )
        sub.actif = True
        sub.fin = None
        sub.save()
        return Response(
            {"detail": "Abonnement activé avec succès.", "created": created},
            status=status.HTTP_200_OK
        )

    # --- Se désabonner ---
    @action(detail=True, methods=["post"], permission_classes=[Est_ce_que_le_vendeur])
    def unsubscribe(self, request, pk=None):
        boutique = self.get_object()
        try:
            sub = AbonnementFournisseur.objects.get(
                fournisseur=request.user, boutique=boutique, actif=True
            )
            sub.actif = False
            sub.fin = timezone.now()
            sub.save()
            return Response({"detail": "Abonnement désactivé avec succès."})
        except AbonnementFournisseur.DoesNotExist:
            return Response(
                {"detail": "Pas d'abonnement actif"},
                status=status.HTTP_400_BAD_REQUEST
            )



class CategorieViewSet(viewsets.ModelViewSet):
       queryset = Categorie.objects.all().order_by("nom")
       serializer_class = Est_ce_que_le_vendeur

       def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsSiteAdmin()]
        return [permissions.AllowAny()]

class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.filter(actif=True).select_related("boutique", "categorie")
    serializer_class = ProduitSerializer
    filterset_fields = ["boutique", "categorie"]
    search_fields = ["nom", "description"]
    ordering_fields = ["prix", "cree_a"]


    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [Est_ce_que_le_vendeur()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        Boutique = serializer.validated_data.get("Boutique")
        has_sub = VendorSubscription.objects.filter(vendor=self.request.user, shop=Boutique, active=True).exists()
        if not has_sub:
            raise permissions.PermissionDenied("Vous devez être abonné à cette boutique pour ajouter des produits.")
        serializer.save(vendor=self.request.user)

    def perform_update(self, serializer):
        Boutique = serializer.validated_data.get("Boutique")
        has_sub = VendorSubscription.objects.filter(vendor=self.request.user, shop=Boutique, active=True).exists()
        if not has_sub:
            raise permissions.PermissionDenied("Vous devez être abonné à cette boutique pour mettre à jour des produits.")
        serializer.save(vendor=self.request.user)


class CommandeViewSet(viewsets.ModelViewSet):
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.Est_ce_que_le_vendeur:
            return Commande.objects.filter(client=user).order_by("-created_at")
        return Commande.objects.filter(vendor=user).order_by("-created_at")

    def  perform_create(self, serializer):
        Commande = serializer.save()
        Notification.objects.create(
            user=self.request.user,
            message=f"Votre commande a été créée avec succès : {Commande.id}"
        )

    @action(detail=False, methods=["get"], permission_classes=[Est_ce_que_le_vendeur])
    def vendor_orders(self, request):
        orders = Commande.objects.filter(items__produit__vendor=request.user).distinct().order_by("-created_at")
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = CommandeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            serializer = CommandeSerializer(orders, many=True)
            return Response(serializer.data)

        @api_view(["POST"])
        @permission_classes([permissions.IsAuthenticated])
        def initiate_payment(request):
            serializer = PaymentSerializer(data=request.data)
            if serializer.is_valid():
                payment = serializer.save(status="en_attente")
                Notification.objects.create(
                    user=payment.order.client, 
                    message=f"Votre paiement pour la commande {payment.order.id} a été initié."
                )
                return Response(
                    PaymentSerializer(payment).data, 
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
            PaymentSerializer(payment).data, 
            status=status.HTTP_201_CREATED
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        @api_view(["POST"])
        @permission_classes([permissions.AllowAny])
        def payment_webhook(request):
            event = request.data.get("event")
            data = request.data.get("data", {})

        if event == "payment.succeeded":
            payment_id = data.get("order_id")
            try:
                payment = Paiement.objects.get(pk=payment_id)
                payment.status = "termine"
                payment.save(update_fields=["status"])
                Notification.objects.create(
                    user=payment.order.client, 
                    message=f"Votre paiement pour la commande {payment.order.id} a été confirmé."
                )
                return Response({"status": "success"})
            except Paiement.DoesNotExist:
                return Response({"detail": "commande non trouvée"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status": "ignored"})

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by("-created_at")
    return Response(NotificationSerializer(notifs, many=True).data)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        notifs = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"detail": "notification non trouvée"}, status=status.HTTP_404_NOT_FOUND)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return Response({"detail": "ok"})
