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


class PregnancyTracker(models.Model):
    last_period_date = models.DateField()
    expected_delivery_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expected_delivery_date and self.last_period_date:
            # Calculate expected delivery date (40 weeks from last period)
            self.expected_delivery_date = self.last_period_date + timedelta(days=280)
        super().save(*args, **kwargs)


class ChildVaccination(models.Model):
    child_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)


class VaccinationRecord(models.Model):
    VACCINE_CHOICES = [
        ("bcg", "BCG (যক্ষ্মা)"),
        ("opv0", "OPV-0 (পোলিও)"),
        ("penta1", "Penta-1 (পেন্টাভ্যালেন্ট)"),
        ("penta2", "Penta-2 (পেন্টাভ্যালেন্ট)"),
        ("penta3", "Penta-3 (পেন্টাভ্যালেন্ট)"),
        ("mr1", "MR-1 (হাম ও রুবেলা)"),
        ("mr2", "MR-2 (হাম ও রুবেলা)"),
    ]

    child = models.ForeignKey(ChildVaccination, on_delete=models.CASCADE)
    vaccine_type = models.CharField(max_length=20, choices=VACCINE_CHOICES)
    scheduled_date = models.DateField()
    administered_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)


class HealthEvent(models.Model):
    EVENT_TYPES = [
        ("health_camp", "স্বাস্থ্য ক্যাম্প"),
        ("vaccination", "টিকাদান কর্মসূচী"),
        ("screening", "স্বাস্থ্য স্ক্রীনিং"),
        ("awareness", "সচেতনতা সেশন"),
        ("blood_donation", "রক্তদান শিবির"),
    ]

    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    description = models.TextField()
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.TextField()
    upazila = models.CharField(max_length=100)
    union = models.CharField(max_length=100)
    organizer = models.CharField(max_length=200)
    contact = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["date", "start_time"]


class HealthWorker(models.Model):
    SKILL_CHOICES = [
        ("mental_health", "মানসিক স্বাস্থ্য"),
        ("first_aid", "প্রাথমিক চিকিৎসা"),
        ("maternal_health", "মাতৃস্বাস্থ্য"),
        ("child_health", "শিশু স্বাস্থ্য"),
        ("chronic_disease", "দীর্ঘমেয়াদী রোগ (ডায়াবেটিস/বিপি)"),
        ("vaccination", "টিকাদান"),
        ("health_education", "স্বাস্থ্য শিক্ষা"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    whatsapp_available = models.BooleanField(default=False)
    village = models.CharField(max_length=100)
    union = models.CharField(max_length=100)
    upazila = models.CharField(max_length=100)
    skills = models.CharField(max_length=200)  # Comma-separated skills
    training_organization = models.CharField(max_length=200)
    available_hours = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    languages = models.CharField(max_length=100, default="বাংলা")

    def __str__(self):
        return self.name
