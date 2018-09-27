'''
Email active volunteers the rota vacancies.
Intended to be run as a cron job. In the cron file,
both python and manage.py will need their full paths.
TODO test exit status of send_mail.
'''

import datetime
from collections import OrderedDict
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q
from django.urls import reverse
import django.utils.timezone as timezone

from toolkit.diary.models import Showing
from toolkit.members.models import Volunteer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SUBJECT = ('Rota vacancies at %s commencing %s' %
           (settings.VENUE['cinemaname'],
            datetime.datetime.now().strftime('%d %B %Y'))
           )


class Command(BaseCommand):
    help = "Email volunteers the rota vacancies"

    # Brutally adapted from view_rota_vacancies in diary/edit_views.py
    # In a better world I would have used the above function passing it
    # the appropriate request
    def _view_rota_vacancies(self, user):
        days_ahead = settings.ROTA_DAYS_AHEAD
        start = timezone.now()
        end_date = start + datetime.timedelta(days=days_ahead)
        showings = (Showing.objects.not_cancelled()
                                   .confirmed()
                                   .start_in_range(start, end_date)
                                   .order_by('start')
                                   .prefetch_related('rotaentry_set__role')
                                   .select_related())
        showings_vacant_roles = OrderedDict(
            (
                showing,
                showing.rotaentry_set.filter(Q(name="") | Q(name__isnull=True))
            ) for showing in showings
        )

        # Surprisingly round-about way to get tomorrow's date:
        now_local = timezone.localtime(timezone.now())

        context = {
            'user': user,
            'days_ahead': days_ahead,
            'now': now_local,
            'now_plus_1d': now_local + datetime.timedelta(days=1),
            'VENUE': settings.VENUE,
            'showings_vacant_roles': showings_vacant_roles,
        }
        return render_to_string('view_rota_vacancies_email.html', context)

    def handle(self, *args, **options):

        # vols = Volunteer.objects.filter(active=True)
        # FIXME remove test code
        vols = (Volunteer.objects.filter(active=True)
                                 .filter(Q(member__volunteer__user__username="ChristoWallers") |
                                         Q(member__volunteer__user__username="MarcusValentine")))
        logger.info('Emailing rota to %d volunteers...' % vols.count())

        # print(vacancies_txt)
        vacancies_plain = ("%s rota roles that need filling in the next %d days.\nSee the full rota at %s%s" %
                           (settings.VENUE['longname'],
                            settings.ROTA_DAYS_AHEAD,
                            settings.VENUE['url'],
                            reverse('rota-edit')
                            ))

        for vol in vols:
            self.stdout.write('Emailing %s <%s> %s' % (
                vol.member.name,
                vol.member.email,
                vol.member.volunteer.user.username  # TODO Test this exists
                ))

            vacancies_html = self._view_rota_vacancies(
                vol.member.volunteer.user.username)

            send_mail(SUBJECT,
                      vacancies_plain,
                      settings.VENUE['mailout_from_address'],
                      [vol.member.email],
                      html_message=vacancies_html,
                      fail_silently=False,
                      )

        self.stdout.write(self.style.SUCCESS(
            '\nEmailed %d vols\n' % len(vols)))
