from django.urls import path
from . import views

urlpatterns = [
    path("mood-tracker/", views.mood_tracker, name="mood_tracker"),
    path("health-map/", views.health_map, name="health_map"),
    path("help-request/", views.help_request, name="help_request"),
]
