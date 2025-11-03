from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("mood-tracker/", views.mood_tracker, name="mood_tracker"),
    path("health-map/", views.health_map, name="health_map"),
    path("help-request/", views.help_request, name="help_request"),
    path("health-tips/", views.health_tips, name="health_tips"),
    path("maternal-tracker/", views.maternal_tracker, name="maternal_tracker"),
    path("symptom-guide/", views.symptom_guide, name="symptom_guide"),
    path("health-events/", views.health_events, name="health_events"),
]
