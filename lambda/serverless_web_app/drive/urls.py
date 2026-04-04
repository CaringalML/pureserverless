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
    path("bulk-delete/",                 views.bulk_delete,    name="drive_bulk_delete"),
    path("archive/",                      views.archive_files,  name="drive_archive"),
    path("archive/view/",                 views.archive_view,   name="drive_archive_view"),
    path("restore/<int:pk>/",             views.restore_file,       name="drive_restore"),
    path("restore/",                      views.bulk_restore,       name="drive_bulk_restore"),
    path("bin/",                          views.recycle_bin,        name="drive_bin"),
    path("bin/<int:pk>/restore/",         views.restore_from_bin,   name="drive_bin_restore"),
    path("bin/<int:pk>/delete/",          views.permanent_delete,   name="drive_bin_delete"),
]
