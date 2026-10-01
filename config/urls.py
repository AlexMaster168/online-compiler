from django.contrib import admin
from django.urls import path

from compiler import accounts, views

urlpatterns = [
    path("", views.index, name="index"),
    path("s/<str:snippet_id>/", views.index, name="snippet"),
    path("s/<str:snippet_id>/raw/", views.snippet_raw, name="snippet-raw"),
    path("s/<str:snippet_id>/zip/", views.snippet_zip, name="snippet-zip"),
    path("api/languages/", views.languages, name="api-languages"),
    path("api/run/", views.run, name="api-run"),
    path("api/format/", views.format_code, name="api-format"),
    path("api/zip/", views.project_zip, name="api-zip"),
    path("api/snippets/", views.create_snippet, name="api-snippet-create"),
    path("api/snippets/<str:snippet_id>/", accounts.snippet_detail, name="api-snippet"),
    path("api/snippets/<str:snippet_id>/fork/", accounts.fork, name="api-snippet-fork"),
    path("api/projects/", accounts.projects, name="api-projects"),
    path("api/auth/me/", accounts.me, name="api-me"),
    path("api/auth/register/", accounts.register, name="api-register"),
    path("api/auth/login/", accounts.login_view, name="api-login"),
    path("api/auth/logout/", accounts.logout_view, name="api-logout"),
    path("api/history/", views.history, name="api-history"),
    path("api/executions/<int:execution_id>/", views.execution_detail, name="api-execution"),
    path("admin/", admin.site.urls),
]
