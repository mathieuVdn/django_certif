from django.contrib import admin
from django.contrib import messages
from django.contrib import admin
from .models import ImportHistory

@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    list_display = ("created_at", "max_requests", "results_per_page", "status", "progress")

