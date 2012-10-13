#!/usr/bin/env python
import logging

from toolkit.diary.models import Event, EventTag
from django.db.models import Q


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Set up logging:
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
logger.addHandler(consoleHandler)


def tag_events_with_name_containing(text, tags):
    events = Event.objects.filter(name__icontains=text)
    for tag in tags:
        tag = EventTag.objects.get(name=tag)
        for e in events:
            tag.event_set.add(e)


def tag_events_with_copy_containing(text, tags):
    events = Event.objects.filter(copy__icontains=text)
    for tag in tags:
        tag = EventTag.objects.get(name=tag)
        for e in events:
            tag.event_set.add(e)


def tag_events_with_terms_containing(text, tags):
    events = Event.objects.filter(terms__icontains=text)
    for tag in tags:
        tag = EventTag.objects.get(name=tag)
        for e in events:
            tag.event_set.add(e)


def tag_ttt_as_film():
    # Assume all discounted things are TTT and are film
    ttt = Event.objects.filter(showings__discounted=True)
    tag = EventTag.objects.get(name="film")
    for e in ttt:
        tag.event_set.add(e)
    # Belt and braces:
    tag_events_with_copy_containing("TTT", ("film", "35mm"))


def tag_certs_as_film():
    # Assume all discounted things are TTT and are film
    print "Certificate based guessing"
    certificates = ('PG', 'U', '15', '12', '12A', '18')
    cert_text = []
    cert_text.extend("cert " + c for c in certificates)
    cert_text.extend("cert" + c for c in certificates)
    cert_text.extend("cert." + c for c in certificates)
    cert_text.extend("cert. " + c for c in certificates)
    cert_text.extend("cert:" + c for c in certificates)
    cert_text.extend("cert: " + c for c in certificates)
    cert_text.extend("certificate " + c for c in certificates)
    cert_text.extend("certificate: " + c for c in certificates)
    query = Q()
    for ct in cert_text:
        query = query | Q(copy__icontains=ct)

    events = Event.objects.filter(query)
    tag = EventTag.objects.get(name="film")
    print "Certificates lead to %d events being tagged as films" % len(query)
    for e in events:
        tag.event_set.add(e)
    # Belt and braces:
    tag_events_with_copy_containing("TTT", ("film", "35mm"))


def main():
    copy_map = {
        "nanoplex": ("nanoplex",),
        "babycinema": ("babycinema", "film"),
        "cabaret": ("cabaret", "party"),
        "hkkp": ("hkkp",),
        "rescore": ("film", "music"),
        "documentary": ("film",),
        "indymedia": ('indymedia',),
        "orchestra": ('cubeorchestra',),
        "bluescreen": ('bluescreen',),
    }
    for text, tags in copy_map.iteritems():
        print text, tags
        tag_events_with_terms_containing(text, tags)
        tag_events_with_name_containing(text, tags)

    tag_ttt_as_film()
    tag_certs_as_film()


if __name__ == "__main__":
    main()
