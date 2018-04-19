from django.contrib import admin

from django.conf import settings
from toolkit.diary.models import (Showing, Event, DiaryIdea, MediaItem,
                                  EventTemplate, EventTag, Role, RotaEntry,
                                  PrintedProgramme, Room)
from toolkit.members.models import Member, Volunteer, TrainingRecord


admin.site.site_header = settings.VENUE['cinemaname']
admin.site.site_title = settings.VENUE['name']
# Default is Site administration
admin.site.index_title = 'Administration Backend'


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


class VolunteerAdmin(admin.ModelAdmin):
    # TODO get obeject name to return soemthing sensible
    model = Volunteer


class ShowingAdmin(admin.ModelAdmin):
    model = Showing


class EventAdmin(admin.ModelAdmin):
    model = Event


admin.site.register(DiaryIdea, DiaryIdeaAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Showing, ShowingAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Volunteer, VolunteerAdmin)
