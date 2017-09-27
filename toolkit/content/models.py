from django.db import models

from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from modelcluster.fields import ParentalKey


class BasicArticlePage(Page):
    body = RichTextField(blank=False)
    image = models.ForeignKey(
            'wagtailimages.Image', on_delete=models.SET_NULL, related_name='+',
            null=True, blank=True
    )

    content_panels = Page.content_panels + [
            FieldPanel('body', classname='full'),
            ImageChooserPanel('image'),
    ]

class ImageGalleryPage(Page):
    intro_text = RichTextField(blank=True)

    footer_text = RichTextField(blank=True)

    content_panels = Page.content_panels + [
            FieldPanel('intro_text'),
            InlinePanel('gallery_images'),
            FieldPanel('footer_text'),
    ]


class ImageGalleryImage(Orderable):
    page = ParentalKey(ImageGalleryPage, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+')
    caption = models.CharField(blank=True, max_length=255)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
