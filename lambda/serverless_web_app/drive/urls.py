from django.urls import path
from . import views

urlpatterns = [
    path("",                        views.drive_home,      name="drive_home"),
    path("upload-url/",             views.upload_url,      name="drive_upload_url"),
    path("confirm/",                views.confirm_upload,  name="drive_confirm"),
    path("view/<int:pk>/",          views.view_file,       name="drive_view"),
    path("delete/<int:pk>/",        views.delete_file,     name="drive_delete"),
    path("archive/",                views.archive_files,   name="drive_archive"),
]
