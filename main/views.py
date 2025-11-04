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


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HealthTip, Hospital
import random

def home(request):
    return render(request, 'index.html')

def voice_assistant(request):
    return render(request, 'voice_assistant.html')

@csrf_exempt
def process_voice_command(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command = data.get('command', '').lower()
            language = detect_language(command)
            
            response = generate_response(command, language)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def detect_language(text):
    """Detect if text is Bengali, English, or mixed"""
    bengali_chars = set('অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়')
    has_bengali = any(char in bengali_chars for char in text)
    has_english = any(char.isalpha() for char in text if char not in bengali_chars)
    
    if has_bengali and has_english:
        return 'mixed'
    elif has_bengali:
        return 'bn'
    else:
        return 'en'

def generate_response(command, language):
    """Generate appropriate response based on voice command"""
    
    # Bengali commands
    bn_responses = {
        'স্বাস্থ্য তথ্য দেখাও': get_health_tip('bn'),
        'হাসপাতাল কোথায়': get_nearest_hospital('bn'),
        'আমি আজ কেমন আছি': mood_check('bn'),
        'সাহায্য কর': get_help('bn'),
        'হেল্প': get_help('bn'),
    }
    
    # English commands
    en_responses = {
        'show health info': get_health_tip('en'),
        'where is hospital': get_nearest_hospital('en'),
        'how am i today': mood_check('en'),
        'help me': get_help('en'),
        'help': get_help('en'),
    }
    
    # Mixed language commands
    mixed_responses = {
        'tumi amk aktu help kroba': get_help('mixed'),
        'help korba': get_help('mixed'),
    }
    
    # Check command in all language dictionaries
    if command in bn_responses:
        return bn_responses[command]
    elif command in en_responses:
        return en_responses[command]
    elif command in mixed_responses:
        return mixed_responses[command]
    else:
        return unknown_command(language)

def get_health_tip(language):
    """Get a random health tip in the specified language"""
    tips = HealthTip.objects.filter(language=language)
    if tips.exists():
        tip = random.choice(tips)
        return {
            'type': 'health_tip',
            'message': tip.content,
            'speech': tip.content,
            'language': language
        }
    else:
        default_tips = {
            'bn': 'নিয়মিত হাঁটাহাঁটি করুন এবং পর্যাপ্ত পানি পান করুন।',
            'en': 'Walk regularly and drink plenty of water.',
            'mixed': 'Regularly walk koren and plenty water drink korben.'
        }
        return {
            'type': 'health_tip',
            'message': default_tips.get(language, default_tips['en']),
            'speech': default_tips.get(language, default_tips['en']),
            'language': language
        }

def get_nearest_hospital(language):
    """Get nearest hospital information"""
    hospitals = Hospital.objects.all()
    if hospitals.exists():
        hospital = hospitals.first()  # In real app, use geolocation
        messages = {
            'bn': f'নিকটবর্তী হাসপাতাল: {hospital.name}, ঠিকানা: {hospital.address}',
            'en': f'Nearest hospital: {hospital.name}, Address: {hospital.address}',
            'mixed': f'Nearest hospital: {hospital.name}, Address: {hospital.address}'
        }
        return {
            'type': 'hospital_info',
            'message': messages.get(language, messages['en']),
            'speech': messages.get(language, messages['en']),
            'language': language
        }
    else:
        messages = {
            'bn': 'দুঃখিত, এখনই হাসপাতালের তথ্য পাওয়া যাচ্ছে না।',
            'en': 'Sorry, hospital information is not available right now.',
            'mixed': 'Sorry, hospital information currently available nei.'
        }
        return {
            'type': 'hospital_info',
            'message': messages.get(language, messages['en']),
            'speech': messages.get(language, messages['en']),
            'language': language
        }

def mood_check(language):
    """Perform mood check-in"""
    messages = {
        'bn': 'আপনার দিনটি ভালো কাটুক! আপনার মনের অবস্থা জানাতে চাইলে বলুন "আমার মন ভালো" বা "আমার মন খারাপ"',
        'en': 'Have a great day! To share your mood, say "I am feeling good" or "I am feeling bad"',
        'mixed': 'Apnar din valo katuk! Your mood share korte chaile bollen "ami valo achi" or "ami kharap achi"'
    }
    return {
        'type': 'mood_check',
        'message': messages.get(language, messages['en']),
        'speech': messages.get(language, messages['en']),
        'language': language
    }

def get_help(language):
    """Provide help information"""
    messages = {
        'bn': 'আপনি বলতে পারেন: "স্বাস্থ্য তথ্য দেখাও", "হাসপাতাল কোথায়", "আমি আজ কেমন আছি"',
        'en': 'You can say: "show health info", "where is hospital", "how am I today"',
        'mixed': 'Apni bolte paren: "health info dekhao", "hospital kothay", "ami aj kemon achi"'
    }
    return {
        'type': 'help',
        'message': messages.get(language, messages['en']),
        'speech': messages.get(language, messages['en']),
        'language': language
    }

def unknown_command(language):
    """Handle unknown commands"""
    messages = {
        'bn': 'দুঃখিত, আমি এই কথাটি বুঝতে পারিনি। সাহায্যের জন্য বলুন "সাহায্য কর"',
        'en': 'Sorry, I did not understand that. For help, say "help me"',
        'mixed': 'Sorry, ami bujhte parini. Help er jonno bollen "help korba"'
    }
    return {
        'type': 'unknown',
        'message': messages.get(language, messages['en']),
        'speech': messages.get(language, messages['en']),
        'language': language
    }



from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import HealthTip, Hospital
from .ai_service import AIService, HealthAPIService
import random

ai_service = AIService()
health_api = HealthAPIService()

def home(request):
    return render(request, 'index.html')

def voice_assistant(request):
    return render(request, 'voice_assistant.html')

@csrf_exempt
def process_voice_command(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command = data.get('command', '').lower()
            language = detect_language(command)
            
            # Use AI service for intelligent responses
            response = process_with_ai(command, language)
            return JsonResponse(response)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def detect_language(text):
    """Detect if text is Bengali, English, or mixed"""
    bengali_chars = set('অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়')
    has_bengali = any(char in bengali_chars for char in text)
    has_english = any(char.isalpha() for char in text if char not in bengali_chars)
    
    if has_bengali and has_english:
        return 'mixed'
    elif has_bengali:
        return 'bn'
    else:
        return 'en'

def process_with_ai(command, language):
    """Process command using AI service for intelligent responses"""
    
    # Check for specific commands first
    specific_commands = {
        'bn': {
            'স্বাস্থ্য তথ্য দেখাও': get_health_tip,
            'হাসপাতাল কোথায়': get_nearest_hospital,
            'আমি আজ কেমন আছি': mood_check,
            'সাহায্য কর': get_help,
            'হেল্প': get_help,
            'জরুরী': handle_emergency,
        },
        'en': {
            'show health info': get_health_tip,
            'where is hospital': get_nearest_hospital,
            'how am i today': mood_check,
            'help me': get_help,
            'help': get_help,
            'emergency': handle_emergency,
        },
        'mixed': {
            'health info dekhao': get_health_tip,
            'hospital kothay': get_nearest_hospital,
            'ami aj kemon achi': mood_check,
            'help korba': get_help,
            'emergency help': handle_emergency,
        }
    }
    
    # Check if it's a specific command
    for lang_commands in specific_commands.values():
        if command in lang_commands:
            return lang_commands[command](language)
    
    # Use AI for general conversation and health queries
    return handle_general_query(command, language)

def handle_general_query(command, language):
    """Handle general queries using AI"""
    ai_response = ai_service.get_ai_response(command, language, 'health')
    
    return {
        'type': 'ai_response',
        'message': ai_response,
        'speech': ai_response,
        'language': language
    }

def handle_emergency(language):
    """Handle emergency situations"""
    messages = {
        'bn': 'জরুরী সাহায্যের জন্য, অনুগ্রহ করে立即 নিকটবর্তী হাসপাতালে যোগাযোগ করুন। জরুরী নম্বর: ৯৯৯',
        'en': 'For emergency help, please contact the nearest hospital immediately. Emergency number: 999',
        'mixed': 'Emergency help er jonno, please immediately nearest hospital e contact korun. Emergency number: 999'
    }
    
    return {
        'type': 'emergency',
        'message': messages.get(language, messages['en']),
        'speech': messages.get(language, messages['en']),
        'language': language
    }

def get_health_tip(language):
    """Get AI-powered health tip"""
    prompts = {
        'bn': 'আমাকে একটি স্বাস্থ্য টিপস দিন বাংলায়। খুব সংক্ষিপ্ত করুন।',
        'en': 'Give me a health tip in English. Keep it very brief.',
        'mixed': 'Amake ekta health tip din. Very short korun.'
    }
    
    ai_tip = ai_service.get_ai_response(prompts.get(language, prompts['bn']), language, 'health')
    
    return {
        'type': 'health_tip',
        'message': ai_tip,
        'speech': ai_tip,
        'language': language
    }

def get_nearest_hospital(language):
    """Get nearest hospital information with AI enhancement"""
    hospitals = Hospital.objects.all()
    if hospitals.exists():
        hospital = hospitals.first()
        
        # Use AI to make the response more natural
        prompt = f"""
        Tell me about the nearest hospital: {hospital.name}, Address: {hospital.address}.
        Make it sound natural and helpful in {language} language. Keep it very brief.
        """
        
        ai_response = ai_service.get_ai_response(prompt, language, 'general')
        
        return {
            'type': 'hospital_info',
            'message': ai_response,
            'speech': ai_response,
            'language': language
        }
    else:
        messages = {
            'bn': 'দুঃখিত, এখনই হাসপাতালের তথ্য পাওয়া যাচ্ছে না। অনুগ্রহ করে পরে আবার চেষ্টা করুন।',
            'en': 'Sorry, hospital information is not available right now. Please try again later.',
            'mixed': 'Sorry, hospital information currently available nei. Please try again later.'
        }
        return {
            'type': 'hospital_info',
            'message': messages.get(language, messages['en']),
            'speech': messages.get(language, messages['en']),
            'language': language
        }

def mood_check(language):
    """Enhanced mood check with AI sentiment analysis"""
    messages = {
        'bn': 'আপনার দিনটি ভালো কাটুক! আপনার অনুভূতি শেয়ার করতে চাইলে বলুন। আমি শুনছি...',
        'en': 'Have a great day! If you want to share your feelings, I am listening...',
        'mixed': 'Apnar din valo katuk! Your feelings share korte chaile bollen. Ami shunchi...'
    }
    
    return {
        'type': 'mood_check',
        'message': messages.get(language, messages['en']),
        'speech': messages.get(language, messages['en']),
        'language': language,
        'awaiting_mood': True
    }

@csrf_exempt
def process_mood_response(request):
    """Process mood response with sentiment analysis"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mood_text = data.get('mood_text', '')
            language = data.get('language', 'bn')
            
            sentiment = ai_service.analyze_sentiment(mood_text, language)
            
            responses = {
                'positive': {
                    'bn': 'ভালো খবর! আপনার ভালো অনুভূতি জানতে পেরে আমি খুশি। ভালো থাকুন!',
                    'en': 'Great to hear! Happy to know you are feeling good. Stay well!',
                    'mixed': 'Valo khobor! Apni valo achen jante pere ami khushi. Valo thakun!'
                },
                'negative': {
                    'bn': 'আমি বুঝতে পারছি আপনি খারাপ অনুভূত হচ্ছেন। মনে রাখবেন, সাহায্যের জন্য মানুষ আছে। যদি বেশি খারাপ লাগে, একজন কাছের মানুষকে বলুন।',
                    'en': 'I understand you are feeling down. Remember, help is available. If it gets worse, talk to someone close.',
                    'mixed': 'Ami bujhte parchi apni kharap feel korchen. Remember, help available. Jodi beshi kharap lage, kacher manushke bolun.'
                },
                'neutral': {
                    'bn': 'ধন্যবাদ আপনার অনুভূতি শেয়ার করার জন্য। আপনার দিনটি শুভ হোক!',
                    'en': 'Thank you for sharing your feelings. Have a blessed day!',
                    'mixed': 'Thanks your feelings share korar jonno. Apnar din shubho hok!'
                }
            }
            
            response_data = responses.get(sentiment, responses['neutral'])
            
            return JsonResponse({
                'type': 'mood_response',
                'message': response_data.get(language, response_data['bn']),
                'speech': response_data.get(language, response_data['bn']),
                'sentiment': sentiment,
                'language': language
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def get_help(language):
    """Enhanced help with AI"""
    prompts = {
        'bn': 'মন বন্ধু ভয়েস সহায়ক সম্পর্কে একটি সহায়ক বার্তা তৈরি করুন। আমি কী বলতে পারি? খুব সংক্ষিপ্ত করুন।',
        'en': 'Create a helpful message about Mon Bondhu voice assistant. What can I say? Keep it very brief.',
        'mixed': 'Mon Bondhu voice assistant somporke helpful message create korun. Ami ki bolte pari? Very short korun.'
    }
    
    ai_help = ai_service.get_ai_response(prompts.get(language, prompts['bn']), language, 'general')
    
    return {
        'type': 'help',
        'message': ai_help,
        'speech': ai_help,
        'language': language
    }