from django.db import models

from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from modelcluster.fields import ParentalKey


class BasicArticlePage(Page):
    LEFT = "L"
    RIGHT = "R"

    IMAGE_ALIGNMENTS = (
        (LEFT, 'Left'),
        (RIGHT, 'Right'),
    )

    body = RichTextField(blank=False)
    image = models.ForeignKey(
            'wagtailimages.Image', on_delete=models.SET_NULL, related_name='+',
            null=True, blank=True
    )
    image_alignment = models.CharField(
        max_length=3, choices=IMAGE_ALIGNMENTS, default=LEFT)

    content_panels = Page.content_panels + [
            FieldPanel('body'),
            FieldPanel('image_alignment'),
            ImageChooserPanel('image'),
    ]
    settings_panels = None


class ImageGalleryPage(Page):
    intro_text = RichTextField(blank=True)

    footer_text = RichTextField(blank=True)

    content_panels = Page.content_panels + [
            FieldPanel('intro_text'),
            InlinePanel('gallery_images'),
            FieldPanel('footer_text'),
    ]
    settings_panels = None


class ImageGalleryImage(Orderable):
    page = ParentalKey(ImageGalleryPage, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+')
    caption = models.CharField(blank=True, max_length=255)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
