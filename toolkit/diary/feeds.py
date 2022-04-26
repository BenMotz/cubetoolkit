import datetime

from django.contrib.syndication.views import Feed
from django.urls import reverse
import django.utils.timezone as timezone
from django.conf import settings

from toolkit.diary.models import Showing


class BasicWhatsOnFeed(Feed):
    # Generate a, err, basic "What's on" feed. Defines various methods that
    # hook into the django magic...
    DAYS_AHEAD = 7
    title = "%s cinema forthcoming events" % settings.VENUE["name"]
    description = "Events at the %s cinema over the next %d days. E&OE." % (
        settings.VENUE["cinemaname"],
        DAYS_AHEAD,
    )
    link = "/programme"

    def items(self):
        startdate = timezone.now()
        enddate = startdate + datetime.timedelta(days=self.DAYS_AHEAD)
        showings = (
            Showing.objects.public()
            .start_in_range(startdate, enddate)
            .order_by("start")
            .select_related()
            .select_related()
        )
        return showings.all()

    def item_title(self, showing):
        return showing.event.name

    def item_description(self, showing):
        description = (
            showing.start.strftime("%d/%m/%Y %H:%M<br><br>")
            + showing.event.copy_html
        )
        return description

    def item_link(self, showing):
        # Add the showing ID at the end to ensure that this link is unique (cf.
        # RSS spec)
        return reverse(
            "single-event-view", kwargs={"event_id": showing.event_id}
        )
