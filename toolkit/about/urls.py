from django.conf.urls import patterns, url
from django.views.generic import TemplateView

about_urls = patterns(
    'toolkit.about.views',

    # About the Cube
    url(r'^$', TemplateView.as_view(template_name='template_about.html'),
        name="about"),
    # Volunteering at the Cube
    url(r'^volunteer/$', TemplateView.as_view(template_name='template_volunteer.html'),
        name="about-volunteer"),
    # Contact
    url(r'^contact/$', TemplateView.as_view(template_name='template_directions.html'),
        name="about-contact"),
    # Directions
    url(r'^directions/$', TemplateView.as_view(template_name='template_directions.html'),
        name="about-directions"),
    # Membership
    url(r'^membership/$', TemplateView.as_view(template_name='template_membership.html'),
        name="about-membership"),
    # Advance Tickets
    url(r'^tickets/$', TemplateView.as_view(template_name='template_tickets.html'),
        name="about-tickets"),
    # Tech
    url(r'^tech/$', TemplateView.as_view(template_name='template_tech.html'),
        name="about-tech"),
    # Hire
    url(r'^hire/$', TemplateView.as_view(template_name='template_hire.html'),
        name="about-hire"),
    # Newsletter
    url(r'^newsletter/$', TemplateView.as_view(template_name='template_newsletter.html'),
        name="about-newsletter"),
    # Cube Images
    url(r'^images/$', TemplateView.as_view(template_name='template_images.html'),
        name="about-images"),
    # Babycinema
    url(r'^babycinema/$', TemplateView.as_view(template_name='template_babycinema.html'),
        name="about-babycinema"),
)
