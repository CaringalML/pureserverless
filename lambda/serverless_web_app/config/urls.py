from django.urls import path, include

urlpatterns = [
    path("", include("accounts.urls")),
    path("drive/", include("drive.urls")),
]
