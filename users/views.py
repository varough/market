from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import viewsets, status, permissions 
from rest_framework.decorators import api_view, permission_classes, action 
from rest_framework.response import Response
from rest_framework.authtoken.models import Token 

from .permissions import IsSiteAdmin 

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
