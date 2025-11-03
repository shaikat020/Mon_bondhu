from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import MoodCheckIn, HealthFacility, AnonymousHelpRequest
import json
from django.utils import timezone


def home(request):
    return render(request, "home.html")


def mood_tracker(request):
    if request.method == "POST":
        mood = request.POST.get("mood")
        notes = request.POST.get("notes", "")

        if mood:
            MoodCheckIn.objects.create(mood=mood, notes=notes)
            return JsonResponse({"status": "success"})

    # Get recent mood entries for display
    recent_moods = MoodCheckIn.objects.all()[:10]
    return render(request, "mood_tracker.html", {"recent_moods": recent_moods})


def health_map(request):
    facilities = HealthFacility.objects.all()

    # Filter by upazila if provided
    upazila = request.GET.get("upazila")
    if upazila:
        facilities = facilities.filter(upazila__icontains=upazila)

    return render(request, "health_map.html", {"facilities": facilities})


def help_request(request):
    if request.method == "POST":
        help_type = request.POST.get("help_type")
        description = request.POST.get("description")
        contact_preference = request.POST.get("contact_preference", "")

        AnonymousHelpRequest.objects.create(
            help_type=help_type,
            description=description,
            contact_preference=contact_preference,
        )
        return JsonResponse(
            {"status": "success", "message": "আপনার অনুরোধ সফলভাবে জমা হয়েছে"}
        )

    return render(request, "help_request.html")


def health_tips(request):
    return render(request, "health_tips.html")


def maternal_tracker(request):
    return render(request, "maternal_tracker.html")


def symptom_guide(request):
    return render(request, "symptom_guide.html")


def health_events(request):
    return render(request, "health_events.html")
