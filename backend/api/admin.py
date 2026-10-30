from django.contrib import admin
from .models import InvestmentPrinciple

@admin.register(InvestmentPrinciple)
class InvestmentPrincipleAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'name', 'metric', 'operator', 'threshold')
    list_filter = ('operator', 'metric')
    search_fields = ('identifier', 'name', 'description')
    ordering = ('identifier',)

