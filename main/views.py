from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
import logging

from .models import (
    MoodCheckIn,
    HealthFacility,
    AnonymousHelpRequest,
    OpenRouterChat,
)
from .forms import ChatForm
import json
from django.utils import timezone

logger = logging.getLogger(__name__)


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

    # Chat helper: show recent exchanges and the chat form
    chats = OpenRouterChat.objects.order_by("id")[:20]
    history = []
    for item in chats:
        lines = item.messages.splitlines()
        user_line = lines[0].replace("User: ", "") if len(lines) > 0 else ""
        ai_line = lines[1].replace("AI: ", "") if len(lines) > 1 else ""
        history.append({"user": user_line, "ai": ai_line})

    form = ChatForm()

    return render(
        request,
        "mood_tracker.html",
        {"recent_moods": recent_moods, "chat_form": form, "chat_history": history},
    )


@csrf_protect
def send_message(request):
    """AJAX endpoint used by the mood_tracker chat helper.

    Accepts POST with 'message' and returns JSON {response: str, chat_id: int}.
    Tries to use external AI if OPENAI_API_KEY (or similar) is configured; falls back to echo.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    form = ChatForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Message is required."}, status=400)

    user_message = form.cleaned_data["message"].strip()
    if not user_message:
        return JsonResponse({"error": "Message is required."}, status=400)

    ai_response = None
    api_key = getattr(settings, "OPENAI_API_KEY", None)

    try:
        if api_key:
            # Try to use google genai if available (best-effort). If not installed, we'll fall back.
            from google import genai  # type: ignore

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_message,
            )
            ai_response = (
                response.text.strip()
                if response and hasattr(response, "text") and response.text
                else None
            )
    except Exception as e:  # pragma: no cover - best-effort external call
        logger.warning("External AI call failed: %s", e)

    if not ai_response:
        # Gentle, empathetic fallback tailored for the mood tracker users
        # Keep language simple and validation-friendly for rural users
        ai_response = (
            "আমি শুনলাম — এটা সহজ নয়। আপনি বলছেন: '" + user_message + "'. "
            "যদি আপনি চান, আমি একটু শান্ত করার কথা বলতে পারি বা সাহায্যের পথ বলব।"
        )

    # Persist the exchange
    chat = OpenRouterChat.objects.create(messages=f"User: {user_message}\nAI: {ai_response}")

    return JsonResponse({"response": ai_response, "chat_id": chat.id}, status=201)


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


def worker_directory(request):
    return render(request, "worker_directory.html")


def data_export(request):
    return render(request, "data_export.html")
