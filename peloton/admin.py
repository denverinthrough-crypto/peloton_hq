from django.contrib import admin
from .models import Team, Specialty, Rider, Race, Stage, StageResult, RaceResult

# Simple registration - no customistaion needed
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'bike_brand']


admin.site.register(Specialty)



# Register your models here.
# Register Team so it shows up in the Django admin panel
@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):

    # Columns to display in the team list
    list_display = ['full_name', 'team', 'nationality', 'age', 'is_active']

    list_filter = ['team', 'specialties', 'nationality', 'is_active']

    # Replaces the ugly multi-select with a clean two-panel picker
    filter_horizontal = ['specialties']

    ordering = ['team', 'last_name']
    search_fields = ['first_name', 'last_name']


@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ['name','year', 'country', 'race_type']
    list_filter = ['race_type', 'year']
    search_fields = ['name']

@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ['rider', 'race', 'finishing_position', 'finish_status']
    list_filter = ['race', 'finish_status']
    search_fields = ['rider__last_name']
    ordering = ['race', 'finishing_position']