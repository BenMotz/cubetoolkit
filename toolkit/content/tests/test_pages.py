import json
import tempfile

from django.core import mail
from django.test import TestCase, override_settings

from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from toolkit.content.models import (
    BasicArticlePage,
    ComplexArticlePage,
    EmailFormPage,
    FormField,
    ImageGalleryImage,
    ImageGalleryPage,
    SectionLink,
    SectionRootWithLinks,
)


class ContentPageTests(TestCase):
    """Check that each type of Wagtail content page renders"""

    def setUp(self):
        # Keep uploaded images and renditions out of the real media dir:
        media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.home = Site.objects.get(is_default_site=True).root_page
        self.image = Image.objects.create(
            title="Test image", file=get_test_image_file()
        )

    def _add_page(self, page, parent=None):
        (parent or self.home).add_child(instance=page)
        page.save_revision().publish()
        return page

    def test_basic_article_page_without_image(self):
        page = self._add_page(
            BasicArticlePage(
                title="Basic article", body="<p>Some body text</p>"
            )
        )
        response = self.client.get(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/basic_article_page.html")
        self.assertContains(response, "<h3>Basic article</h3>", html=True)
        self.assertContains(response, "Some body text")

    def test_basic_article_page_image_alignments(self):
        for alignment in ("L", "C", "R"):
            with self.subTest(alignment=alignment):
                page = self._add_page(
                    BasicArticlePage(
                        title=f"Article {alignment}",
                        slug=f"article-{alignment.lower()}",
                        body="<p>Some body text</p>",
                        image=self.image,
                        image_alignment=alignment,
                    )
                )
                response = self.client.get(page.url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'alt="Test image"')

    def test_complex_article_page(self):
        content = [
            {
                "type": "content_block",
                "value": {
                    "width": 3,
                    "content": [
                        {
                            "type": "rich_text",
                            "value": "<p>Rich text block</p>",
                        }
                    ],
                },
            },
            {
                "type": "content_block",
                "value": {
                    "width": 2,
                    "content": [{"type": "image", "value": self.image.pk}],
                },
            },
            {
                "type": "content_block",
                "value": {
                    "width": 1,
                    "content": [
                        {
                            "type": "raw_html",
                            "value": "<b>Raw HTML block</b>",
                        }
                    ],
                },
            },
        ]
        page = self._add_page(
            ComplexArticlePage(
                title="Complex article", content=json.dumps(content)
            )
        )
        response = self.client.get(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/complex_article_page.html")
        self.assertContains(response, "Rich text block")
        self.assertContains(response, "<b>Raw HTML block</b>", html=True)
        self.assertContains(response, 'alt="Test image"')
        self.assertContains(response, "grid-item--width3")

    def test_image_gallery_page(self):
        page = self._add_page(
            ImageGalleryPage(
                title="Gallery",
                intro_text="<p>Gallery intro</p>",
                footer_text="<p>Gallery footer</p>",
                gallery_images=[
                    ImageGalleryImage(image=self.image, caption="A caption")
                ],
            )
        )
        response = self.client.get(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/image_gallery_page.html")
        self.assertContains(response, "Gallery intro")
        self.assertContains(response, "A caption")
        self.assertContains(response, 'alt="Test image"')

    def test_email_form_page(self):
        page = self._add_page(
            EmailFormPage(
                title="Contact us",
                intro="<p>Form intro</p>",
                thank_you_text="<p>Thanks for that</p>",
                image=self.image,
                to_address="dest@example.com",
                from_address="from@example.com",
                subject="Form submission",
                form_fields=[
                    FormField(
                        label="Your name",
                        field_type="singleline",
                        required=True,
                    )
                ],
            )
        )
        response = self.client.get(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "content/email_form_page.html")
        self.assertContains(response, "Form intro")
        self.assertContains(response, 'name="your_name"')

        response = self.client.post(page.url, {"your_name": "Someone"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "content/email_form_page_landing.html"
        )
        self.assertContains(response, "Thanks for that")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["dest@example.com"])
        self.assertIn("Someone", mail.outbox[0].body)

    def test_section_root_is_not_served_but_links_appear_in_menu(self):
        section = self._add_page(
            SectionRootWithLinks(
                title="Section menu",
                show_in_menus=True,
                links=[SectionLink(link="/elsewhere/", text="Elsewhere")],
            )
        )
        child = self._add_page(
            BasicArticlePage(
                title="Child article",
                body="<p>Child body</p>",
                show_in_menus=True,
            ),
            parent=section,
        )

        response = self.client.get(section.url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(child.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Section menu")
        self.assertContains(
            response, f'<a href="{child.url}">Child article</a>', html=True
        )
        self.assertContains(
            response, '<a href="/elsewhere/">Elsewhere</a>', html=True
        )
