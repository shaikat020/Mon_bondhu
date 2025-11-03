from django.db import models


class MoodCheckIn(models.Model):
    MOOD_CHOICES = [
        ("happy", "😊 খুব ভালো"),
        ("neutral", "😐 ঠিক আছে"),
        ("sad", "😔 কিছুটা খারাপ"),
        ("anxious", "😰 চিন্তিত"),
        ("angry", "😠 রাগান্বিত"),
    ]

    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class HealthFacility(models.Model):
    FACILITY_TYPES = [
        ("clinic", "কমিউনিটি ক্লিনিক"),
        ("hospital", "হাসপাতাল"),
        ("pharmacy", "ফার্মেসি"),
        ("chw", "কমিউনিটি স্বাস্থ্যকর্মী"),
    ]

    name = models.CharField(max_length=200)
    facility_type = models.CharField(max_length=20, choices=FACILITY_TYPES)
    address = models.TextField()
    upazila = models.CharField(max_length=100)
    union = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, blank=True)
    hours = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class AnonymousHelpRequest(models.Model):
    HELP_TYPES = [
        ("mental_health", "মানসিক স্বাস্থ্য সহায়তা"),
        ("physical_health", "শারীরিক স্বাস্থ্য সমস্যা"),
        ("emergency", "জরুরী সাহায্য প্রয়োজন"),
        ("other", "অন্যান্য"),
    ]

    help_type = models.CharField(max_length=20, choices=HELP_TYPES)
    description = models.TextField()
    contact_preference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
