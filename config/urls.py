from django.contrib import admin
from django.urls import path
from portal import views
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("serwery/<slug:slug>/", views.server_detail, name="server"),
    path("aktualnosci/", views.news, name="news"),
    path("poradniki/", views.tutorials, name="tutorials"),
    path("wpis/<slug:slug>/", views.entry_detail, name="entry"),
    path("status/", views.status_json, name="status"),
    path("health/", views.health, name="health"),
]
