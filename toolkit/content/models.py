from collections import OrderedDict

from django.db import models
from django.http import Http404

from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page, Orderable
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    FieldRowPanel,
    StreamFieldPanel,
)
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.edit_handlers import FormSubmissionsPanel
from wagtail.core import blocks
from wagtail.images import blocks as image_blocks
from modelcluster.fields import ParentalKey

import toolkit.diary.models


class BasicArticlePage(Page):
    LEFT = "L"
    CENTRE = "C"
    RIGHT = "R"

    IMAGE_ALIGNMENTS = (
        (LEFT, "Left"),
        (CENTRE, "Centre"),
        (RIGHT, "Right"),
    )

    body = RichTextField(blank=False)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    image_alignment = models.CharField(
        max_length=3, choices=IMAGE_ALIGNMENTS, default=LEFT
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("image_alignment"),
        ImageChooserPanel("image"),
    ]
    settings_panels = None


class EventTagPage(Page):
    body = RichTextField(blank=False)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    event_tag = models.OneToOneField(
        "diary.EventTag",
        related_name="event_tag_page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("event_tag"),
        ImageChooserPanel("image"),
    ]
    settings_panels = None

    def get_context(self, request):
        context = super(EventTagPage, self).get_context(request)
        events = OrderedDict()

        # In MySQL/MariaDB it's apparently more performant to separately
        # run the taq query, then just pass a list into the showings query,
        # than to have a subquery (which is what you'd get if we passed
        # self.event_tags.all() directly into event__tags__in).
        # See note on performance here:
        # https://docs.djangoproject.com/en/1.11/ref/models/querysets/#in
        # (borne out experimentally)
        if self.event_tag:
            showings = (
                toolkit.diary.models.Showing.objects.public()
                .filter(event__tags__in=[self.event_tag])
                .start_in_future()
                .order_by("start")
                .select_related()
                .prefetch_related("event__media")
                .prefetch_related("event__tags")
            )
            # Build a list of events for that list of showings:
            for showing in showings:
                events.setdefault(showing.event, list()).append(showing)

        context["events"] = events
        return context


class WidthBlock(blocks.StructBlock):
    width = blocks.IntegerBlock(
        min_value=1,
        max_value=5,
        help_text="How many grid columns to occupy in rendered template",
    )
    content = blocks.StreamBlock(
        [
            ("rich_text", blocks.RichTextBlock()),
            ("raw_html", blocks.RawHTMLBlock()),
            ("image", image_blocks.ImageChooserBlock()),
        ],
        min_num=1,
        max_num=1,
    )


class ComplexArticlePage(Page):
    content = StreamField(
        [
            ("content_block", WidthBlock()),
        ]
    )
    content_panels = Page.content_panels + [
        StreamFieldPanel("content"),
    ]


class ImageGalleryPage(Page):
    intro_text = RichTextField(blank=True)

    footer_text = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro_text"),
        InlinePanel("gallery_images"),
        FieldPanel("footer_text"),
    ]
    settings_panels = None


class ImageGalleryImage(Orderable):
    page = ParentalKey(ImageGalleryPage, related_name="gallery_images")
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=255)

    panels = [
        ImageChooserPanel("image"),
        FieldPanel("caption"),
    ]


class SectionRootWithLinks(Page):
    content_panels = Page.content_panels + [
        InlinePanel("links", label="Links"),
    ]

    # Hide 'slug', 'SEO title' etc, as they're not relevant:
    promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
            ],
            "Common page configuration",
        )
    ]
    settings_panels = None

    def serve(self, request):
        # For now, don't actually serve anything for this page:
        raise Http404("Page not found")


class SectionLink(Orderable):
    page = ParentalKey(SectionRootWithLinks, related_name="links")

    text = models.CharField(max_length=1024, blank=True, null=False)
    # This is a link (rather than a URLField) to allow relative links
    link = models.CharField(max_length=1024, blank=False, null=False)

    panels = [
        FieldPanel("link"),
        FieldPanel("text"),
    ]


class FormField(AbstractFormField):
    page = ParentalKey("EmailFormPage", related_name="form_fields")


class EmailFormPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )

    content_panels = AbstractEmailForm.content_panels + [
        FormSubmissionsPanel(),
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text"),
        ImageChooserPanel("image"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address", classname="col6"),
                        FieldPanel("to_address", classname="col6"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            "Email",
        ),
    ]
