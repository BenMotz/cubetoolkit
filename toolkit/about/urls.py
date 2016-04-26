from django.conf.urls import patterns, url
from django.views.generic import TemplateView

about_urls = patterns(
    'toolkit.about.views',

    # About the Cube
    url(r'^about/$', TemplateView.as_view(template_name='template_about.html')),
    # Volunteering at the Cube
    url(r'^volunteer/$', TemplateView.as_view(template_name='template_volunteer.html')),
    # Directions
    url(r'^directions/$', TemplateView.as_view(template_name='template_directions.html')),
    # Membership
    url(r'^membership/$', TemplateView.as_view(template_name='template_membership.html')),
    # Advance Tickets
    url(r'^tickets/$', TemplateView.as_view(template_name='template_tickets.html')),
    # Tech
    url(r'^tech/$', TemplateView.as_view(template_name='template_tech.html')),
    # Hire
    url(r'^hire/$', TemplateView.as_view(template_name='template_hire.html')),
    # Newsletter
    url(r'^newsletter/$', TemplateView.as_view(template_name='template_newsletter.html')),
    # Cube Images
    url(r'^images/$', TemplateView.as_view(template_name='template_images.html')),
)
