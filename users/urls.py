from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


urlpatterns = [
   path("auth/register/", register),
   path("auth/login", login),
   path("auth/me", me),
 
 
]