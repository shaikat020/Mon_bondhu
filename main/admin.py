from django.contrib import admin
from . import models


@admin.register(models.MoodCheckIn)
class MoodCheckInAdmin(admin.ModelAdmin):
	list_display = ("id", "mood", "created_at")
	list_filter = ("mood",)
	search_fields = ("notes",)
	ordering = ("-created_at",)


@admin.register(models.HealthFacility)
class HealthFacilityAdmin(admin.ModelAdmin):
	list_display = ("name", "facility_type", "upazila", "union", "contact")
	list_filter = ("facility_type", "upazila")
	search_fields = ("name", "address")


@admin.register(models.AnonymousHelpRequest)
class AnonymousHelpRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "help_type", "created_at", "is_resolved")
	list_filter = ("help_type", "is_resolved")
	search_fields = ("description", "contact_preference")
	readonly_fields = ("created_at",)

	actions = ["mark_resolved"]

	def mark_resolved(self, request, queryset):
		queryset.update(is_resolved=True)

	mark_resolved.short_description = "Mark selected requests as resolved"


@admin.register(models.PregnancyTracker)
class PregnancyTrackerAdmin(admin.ModelAdmin):
	list_display = ("id", "last_period_date", "expected_delivery_date", "created_at")
	readonly_fields = ("expected_delivery_date", "created_at")


@admin.register(models.ChildVaccination)
class ChildVaccinationAdmin(admin.ModelAdmin):
	list_display = ("child_name", "birth_date", "created_at")
	search_fields = ("child_name",)


@admin.register(models.VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"child",
		"vaccine_type",
		"scheduled_date",
		"administered_date",
		"is_completed",
	)
	list_filter = ("vaccine_type", "is_completed")
	search_fields = ("child__child_name",)


@admin.register(models.HealthEvent)
class HealthEventAdmin(admin.ModelAdmin):
	list_display = ("title", "event_type", "date", "upazila", "is_active")
	list_filter = ("event_type", "is_active", "upazila")
	search_fields = ("title", "location")


@admin.register(models.HealthWorker)
class HealthWorkerAdmin(admin.ModelAdmin):
	list_display = ("name", "phone", "village", "upazila", "is_verified")
	search_fields = ("name", "skills")
	list_filter = ("is_verified",)


@admin.register(models.OpenRouterChat)
class OpenRouterChatAdmin(admin.ModelAdmin):
	list_display = ("id", "created_at")
	readonly_fields = ("messages", "created_at")
	search_fields = ("messages",)

