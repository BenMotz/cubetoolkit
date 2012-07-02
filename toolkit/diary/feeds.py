import datetime

import markdown

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from toolkit.diary.models import Showing

class BasicWhatsOnFeed(Feed):
    # Generate a, err, basic "What's on" feed. Defines various methods that hook
    # into the django magic...
    DAYS_AHEAD = 7
    title = "Cube cinema forthcoming events"
    description = "Events at the cube cinema over the next %d days. E&OE." % (DAYS_AHEAD, )
    link = "/diary"

    def items(self):
        startdate = datetime.date.today() #datetime.datetime.now()
        enddate = startdate + datetime.timedelta(days=self.DAYS_AHEAD)
        showings = (Showing.objects.filter(confirmed=True)
                                   .filter(hide_in_programme=False)
                                   .filter(start__range=[startdate, enddate])
                                   .filter(event__private=False)
                                   .order_by('start')
                                   .select_related())
        return showings.all()

    def item_title(self, showing):
        return showing.event.name

    def item_description(self, showing):
        description = showing.start.strftime("%d/%m/%Y %H:%M<br><br>") + markdown.markdown(showing.event.copy)
        return description

    def item_link(self, showing):
        # Add the showing ID at the end to ensure that this link is unique (cf. RSS spec)
        return reverse("single-event-view", kwargs={ 'event_id' : showing.event_id }) + "#" + str(showing.pk)
