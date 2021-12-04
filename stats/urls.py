from os import name
from django.contrib import admin
from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('<str:username>/',views.profile, name = 'profile'),
    path('',views.index,name = 'index'),
]
