#!/usr/bin/env python
from toolkit.diary.models import Event, EventTag


def add_tag(event, tag):
    if not tag.event_set.filter(pk=event.pk):
        print "  %s" % event
        tag.event_set.add(event)


def tag_events_with_field_containing(field, text, tags):
    filter_var = {("%s__icontains" % field): text}
    events = Event.objects.filter(**filter_var)
    for tag in tags:
        tag = EventTag.objects.get(name=tag)
        for e in events:
            add_tag(e, tag)


def tag_ttt_as_film():
    # Assume all discounted things are TTT and are film
    ttt = Event.objects.filter(showings__discounted=True)
    tag = EventTag.objects.get(name="film")
    for e in ttt:
        add_tag(e, tag)


def main():
    copy_map = {
        "nanoplex": ("nanoplex", ),
        "babycinema": ("babycinema", "film"),
        "cabaret": ("cabaret", "party"),
        "rescore": ("film", "music"),
        "documentary": ("film", ),
        "indymedia": ('indymedia', ),
        "orchestra cube": ('cubeorchestra', ),
        "cube orchestra": ('cubeorchestra', ),
        "cubeorchestra": ('cubeorchestra', ),
        "bluescreen": ('bluescreen', ),
        "party": ('party', ),
        "outdoor": ('outdoors', ),
        "q&a": ('q&a', ),
    }
    for text, tags in copy_map.iteritems():
        print "Tagging any events containing the text '%s' with tags '%s':" % (
            text, ", ".join(tags))
        for field in ('terms', 'name'):
            tag_events_with_field_containing(field, text, tags)

    tag_ttt_as_film()


if __name__ == "__main__":
    main()
