from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
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


def voice_assistant(request):
    """Render the voice-first health assistant UI."""
    # Provide a few cached health tips for offline TTS
    cached_tips = [
        "প্রতিদিন পর্যাপ্ত বিশ্রাম নিন এবং পর্যাপ্ত পানি খান।",
        "দীর্ঘক্ষণ চাপ বোধ করলে ৫ মিনিট হাঁটুন বা গভীর শ্বাস নিন।",
        "যদি আপনি মানসিক চাপ বা দুশ্চিন্তায় ভুগছেন, একজন বিশ্বস্ত ব্যক্তির সাথে কথা বলুন।",
    ]
    return render(request, "voice_assistant.html", {"cached_tips": cached_tips})


@csrf_protect
def send_voice_command(request):
    """Handle voice commands sent from the browser.

    Accepts POST with 'command' (recognized Bangla text). Returns JSON {response: str, action: optional}
    Tries to use external AI if available; otherwise uses simple intent mapping for common commands.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    command = request.POST.get("command", "").strip()
    if not command:
        return JsonResponse({"error": "Command is required."}, status=400)

    # Quick local intent mapping for offline/fast responses
    lower = command.lower()

    # Health tips intent
    if any(k in lower for k in ["স্বাস্থ্য তথ্য", "টিপ", "স্বাস্থ্য টিপ", "স্বাস্থ্য তথ্য দেখাও", "টিপ দেখাও"]):
        # pick a cached tip
        tip = (
            "প্রতিদিন পর্যাপ্ত বিশ্রাম নিন এবং পর্যাপ্ত পানি খান।"
        )
        return JsonResponse({"response": tip})

    # Facility intent (hospital location)
    if "হাসপাতাল" in lower or ("কোথ" in lower and "হাসপাতাল" in lower):
        # return nearest hospital if available
        hosp = HealthFacility.objects.filter(facility_type__icontains="hospital")[:1]
        if not hosp:
            hosp = HealthFacility.objects.all()[:1]
        if hosp:
            h = hosp[0]
            resp = f"{h.name}, ঠিকানা: {h.address}. যোগাযোগ: {h.contact or 'নাই'}"
            return JsonResponse({"response": resp})

    # Mood check intent
    if "আমি আজ কেমন" in lower or "আজ কেমন" in lower or "কেমন আছি" in lower:
        resp = (
            "আপনি আজ কেমন মনে করছেন? বলুন: খুব ভালো, ঠিক আছে, কিছুটা খারাপ, চিন্তিত, বা রাগান্বিত। "
            "বলুন এবং আমি সেটি রেকর্ড করব।"
        )
        # store the command in chat history for review
        OpenRouterChat.objects.create(messages=f"User: {command}\nAI: {resp}")
        return JsonResponse({"response": resp, "action": "expect_mood"})

    # Fallback to external AI if API key present
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    ai_response = None
    try:
        if api_key:
            from google import genai  # type: ignore

            client = genai.Client(api_key=api_key)
            # provide a short system prompt to prefer Bangla and action-friendly replies
            prompt = (
                "You are MonBondhu voice assistant speaking Bengali (Bangla). "
                "Respond concisely in Bangla. If the user asks for actions like recording mood or finding hospitals, "
                "answer with a short text and, if applicable, include a JSON-like field 'action' such as 'expect_mood' or 'show_facility'.\n"
                f"User: {command}"
            )
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            ai_response = (
                response.text.strip()
                if response and hasattr(response, "text") and response.text
                else None
            )
    except Exception as e:
        logger.warning("Voice assistant external AI call failed: %s", e)

    if not ai_response:
        # Gentle fallback
        ai_response = (
            "আমি আপনার অনুরোধ বুঝতে পারি না পুরোপুরি, তবে আমি সাহায্য করতে চাই। আপনি 'স্বাস্থ্য তথ্য দেখাও' অথবা 'হাসপাতাল কোথায়' বলতে পারেন।"
        )

    OpenRouterChat.objects.create(messages=f"User: {command}\nAI: {ai_response}")
    return JsonResponse({"response": ai_response})


def help_request(request):
    if request.method == "POST":
        help_type = request.POST.get("help_type")
        description = request.POST.get("description")
        contact_preference = request.POST.get("contact_preference", "")

        req = AnonymousHelpRequest.objects.create(
            help_type=help_type,
            description=description,
            contact_preference=contact_preference,
        )

        # Send an email notification to the support address using EMAIL_HOST_USER
        subject = "[MonBondhu] নতুন গোপন সাহায্য অনুরোধ"
        body = (
            f"Help type: {help_type}\n"
            f"Description: {description}\n"
            f"Contact preference: {contact_preference}\n"
            f"Submitted at: {timezone.now()}\n"
            f"Request id: {req.id}\n"
        )
        from_email = getattr(settings, "EMAIL_HOST_USER", None)
        recipient = ["tahsin.azad.skt@gmail.com"]
        try:
            if from_email:
                send_mail(subject, body, from_email, recipient, fail_silently=False)
            else:
                # If no from_email configured, attempt to send without explicit from (Django will use DEFAULT_FROM_EMAIL)
                send_mail(subject, body, None, recipient, fail_silently=False)
        except BadHeaderError:
            logger.exception("Invalid header found when sending help_request email")
        except Exception:
            # Log and continue — the primary function (storing the request) succeeded
            logger.exception("Failed to send help_request email notification")

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
