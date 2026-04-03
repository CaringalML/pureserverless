from django.urls import path
from . import views

urlpatterns = [
    path("",                              views.drive_home,     name="drive_home"),
    path("folder/<int:folder_pk>/",       views.drive_home,     name="drive_folder"),
    path("folder/create/",                views.create_folder,  name="drive_create_folder"),
    path("folder/<int:pk>/delete/",       views.delete_folder,  name="drive_delete_folder"),
    path("upload-url/",                   views.upload_url,     name="drive_upload_url"),
    path("confirm/",                      views.confirm_upload,  name="drive_confirm"),
    path("download/<int:pk>/",            views.download_file,  name="drive_download"),
    path("view/<int:pk>/url/",            views.get_file_url,   name="drive_file_url"),
    path("view/<int:pk>/",               views.view_file,      name="drive_view"),
    path("delete/<int:pk>/",             views.delete_file,    name="drive_delete"),
    path("archive/",                      views.archive_files,  name="drive_archive"),
]
