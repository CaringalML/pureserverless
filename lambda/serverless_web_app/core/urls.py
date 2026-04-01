from django.urls import path
from . import views

urlpatterns = [
    path("",              views.index,       name="index"),
    path("create/",       views.item_create, name="item_create"),
    path("<int:pk>/",     views.item_detail, name="item_detail"),
    path("<int:pk>/edit/",views.item_update, name="item_update"),
    path("<int:pk>/delete/", views.item_delete, name="item_delete"),
]
