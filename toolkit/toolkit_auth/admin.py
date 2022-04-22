from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django.conf import settings
from toolkit.diary.models import (Showing, Event, DiaryIdea, MediaItem,
                                  EventTemplate, EventTag, Role, RotaEntry,
                                  PrintedProgramme, Room)
from toolkit.members.models import Member, Volunteer, TrainingRecord


admin.site.site_header = settings.VENUE['cinemaname']
admin.site.site_title = settings.VENUE['name']
# Default is Site administration
admin.site.index_title = 'Administration Backend'

UserAdmin.list_display = ('last_name',
                          'username',
                          'volunteer',
                          'email',
                          'is_active',
                          'is_superuser',
                          'date_joined')


class DiaryIdeaAdmin(admin.ModelAdmin):
    # TODO disable creation
    model = DiaryIdea
    list_display = ['month',
                    'ideas']

    list_filter = ['month']

    search_fields = ['ideas']


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ['name',
                    'email',
                    'gdpr_opt_in',
                    'membership_expires',
                    'is_member',
                    'mailout']
    list_filter = ['created_at',
                   'membership_expires',
                   'is_member',
                   'gdpr_opt_in']
    search_fields = ['name',
                     'email']
    ordering = ['name']


class VolunteerAdmin(admin.ModelAdmin):
    # TODO get object name to return soemthing sensible
    model = Volunteer
    list_display = ['member',
                    'user',
                    'active']
    list_filter = ['active']


class ShowingAdmin(admin.ModelAdmin):
    model = Showing


class EventAdmin(admin.ModelAdmin):
    model = Event


class RotaEntryAdmin(admin.ModelAdmin):
    model = RotaEntry


class RoomAdmin(admin.ModelAdmin):
    model = Room


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
# admin.site.register(DiaryIdea, DiaryIdeaAdmin)
# admin.site.register(Event, EventAdmin)
# admin.site.register(Showing, ShowingAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Volunteer, VolunteerAdmin)
# admin.site.register(RotaEntry, RotaEntryAdmin)
admin.site.register(Room, RoomAdmin)
