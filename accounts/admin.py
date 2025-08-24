from django.contrib import admin
from .models import RatesCache

@admin.register(RatesCache)
class RatesCacheAdmin(admin.ModelAdmin):
    list_display = ('from_currency','to_currency','rate','updated_at')
