from django.db import models
from django.http import Http404, HttpResponse

from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    FieldRowPanel,
)
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail import blocks
from wagtail.images import blocks as image_blocks
from modelcluster.fields import ParentalKey


class BasicArticlePage(Page):
    page_description = "Page with a block of text and a single image"

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
    show_on_programme_page = models.BooleanField(
        verbose_name="show on programme pages",
        default=False,
        help_text="Whether a link to this page will appear alongside the main public programme listings",
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("image_alignment"),
        FieldPanel("image"),
    ]
    settings_panels = None
    promote_panels = Page.promote_panels + [
        MultiFieldPanel([FieldPanel("show_on_programme_page")])
    ]


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
            ("image", image_blocks.ImageBlock()),
        ],
        min_num=1,
        max_num=1,
    )


class ComplexArticlePage(Page):
    page_description = (
        "Page with a sequence of multiple text blocks and images"
    )
    content = StreamField(
        [
            ("content_block", WidthBlock()),
        ],
    )
    content_panels = Page.content_panels + [
        FieldPanel("content"),
    ]


class ImageGalleryPage(Page):
    page_description = "An image gallery"
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
        FieldPanel("image"),
        FieldPanel("caption"),
    ]


class SectionRootWithLinks(Page):
    page_description = "Not a real page! Does not have any content, just a bunch of links to go in the site menu"
    content_panels = Page.content_panels + [
        InlinePanel("links", label="Links"),
    ]

    # Hide 'slug', 'SEO title' etc, as they're not relevant:
    promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
                # Remove the following when we get to Wagtail 5.2.4
                # (https://github.com/wagtail/wagtail/issues/11442)
                FieldPanel("slug"),
            ],
            "Common page configuration",
        )
    ]
    settings_panels = None

    def serve(self, request):
        # For now, don't actually serve anything for this page:
        raise Http404("Page not found")

    def serve_preview(self, request, mode_name):
        return HttpResponse(
            b"<html><p>This is not a real page, and does not have "
            b"any content: it's just a collection of links to go in "
            b"the site menu</p>"
        )


class SectionLink(Orderable):
    page = ParentalKey(SectionRootWithLinks, related_name="links")

    text = models.CharField(max_length=1024, blank=True, null=False)
    # This is a CharField, rather than a URLField, to allow relative links:
    link = models.CharField(max_length=1024, blank=False, null=False)

    panels = [
        FieldPanel("link"),
        FieldPanel("text"),
    ]


class FormField(AbstractFormField):
    page = ParentalKey("EmailFormPage", related_name="form_fields")


class EmailFormPage(AbstractEmailForm):
    page_description = "A page with text, an image, and a (configurable) form"
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
        FieldPanel("image"),
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
