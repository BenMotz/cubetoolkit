import django.core.exceptions
from django.http import HttpResponse, Http404
from cube.diary.models import Showing, Event
import subprocess

def test(request):
    return HttpResponse("Testicle")

def view_diary(request, year=None, month=None, day=None):
    return HttpResponse("View_diary: %s %s %s" % (day,month,year))

def view_showing(request, showing_id=None):

    context = {}

    try:
        showing_id = int(showing_id)
        context['showing'] = Showing.objects.get(id=showing_id)
    except django.core.exceptions.ObjectDoesNotExist, ValueError:
        raise Http404("Error: Showing id %s not found" % showing_id)

    # return render_to_response(showing, kk 
    return HttpResponse("View showing %s" % (showing_id))
    
def view_event(request, event_id=None):
    return HttpResponse("View event %s" % (event_id))

