from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsSiteAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff





class  vendeur(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_vendeur)

class Est_propriétaire_ou_en_lecture_seule(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        propriétaire = getattr(obj, 'fournisseur', None) or getattr(obj, 'client', None)
        return propriétaire == request.user 