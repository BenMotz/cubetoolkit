from __future__ import absolute_import
import os.path

import pytz
from datetime import date
import tempfile

from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from toolkit.diary.models import PrintedProgramme

from .common import DiaryTestsMixin


class AddPrintedProgrammeTests(DiaryTestsMixin, TestCase):
    def setUp(self):
        super(AddPrintedProgrammeTests, self).setUp()
        self.client.login(username="admin", password="T3stPassword!")
        self.test_upload = None

    def tearDown(self):
        self.client.logout()
        try:
            if self.test_upload:
                os.unlink(self.test_upload)
        except OSError:
            pass

    def _write_pdf_magic(self, temp_pdf):
        temp_pdf.write('%PDF-1.3\r%\xe2\xe3\xcf\xd3\r\n')
        temp_pdf.seek(0)

    def test_view_loads(self):
        url = reverse("add-printed-programme")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_progamme_invalid_no_file(self):
        url = reverse("add-printed-programme")

        response = self.client.post(url, data={
            "month": "1",
            "year": "2010",
            "designer": u"Designer name",
            "notes": u"Blah blah notes",
            "programme": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_printedprogramme_archive.html")
        self.assertFormError(response, 'new_programme_form', 'programme', u'This field is required.')
        self.assertEqual(PrintedProgramme.objects.count(), 0)

    def test_add_progamme_invalid_file_empty(self):
        url = reverse("add-printed-programme")

        with tempfile.NamedTemporaryFile(
                dir="/tmp", prefix="toolkit-test-programme-", suffix=".pdf") as temp_pdf:
            response = self.client.post(url, data={
                "month": "1",
                "year": "2010",
                "designer": u"Designer name",
                "notes": u"Blah blah notes",
                "programme": temp_pdf,
            })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_printedprogramme_archive.html")
        self.assertFormError(response, 'new_programme_form', 'programme', u'The submitted file is empty.')
        self.assertEqual(PrintedProgramme.objects.count(), 0)

    def test_add_progamme_invalid_duplicate_month(self):
        # Add programme for Jan 1999
        PrintedProgramme(
            month=date(1999, 1, 1),
            designer=u"What?",
            programme="fake/fake"
        ).save()
        url = reverse("add-printed-programme")

        with tempfile.NamedTemporaryFile(
                dir="/tmp", prefix="toolkit-test-programme-", suffix=".pdf") as temp_pdf:
            self._write_pdf_magic(temp_pdf)
            response = self.client.post(url, data={
                "month": "1",
                "year": "1999",
                "designer": u"Designer name",
                "notes": u"Blah blah notes",
                "programme": temp_pdf,
            })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "form_printedprogramme_archive.html")
        self.assertFormError(
            response, 'new_programme_form', 'month',
            u'Printed programme with this Month already exists.'
        )
        # No more objects should have been added:
        self.assertEqual(PrintedProgramme.objects.count(), 1)

    @override_settings(MEDIA_ROOT="/tmp")
    def test_add_progamme(self):
        self.assertEqual(PrintedProgramme.objects.count(), 0)

        url = reverse("add-printed-programme")

        with tempfile.NamedTemporaryFile(
                dir="/tmp", prefix="toolkit-test-programme-", suffix=".pdf") as temp_pdf:
            self._write_pdf_magic(temp_pdf)
            response = self.client.post(url, data={
                "month": "4",
                "year": "2010",
                "designer": u"Designer nam\u0119",
                "notes": u"Blah blah no\u0167es",
                "programme": temp_pdf,
            })
            filename = os.path.basename(temp_pdf.name)
        self.assertRedirects(
            response,
            reverse("edit-printed-programmes")
        )
        # Check file upload:
        expected_upload = os.path.join(u"printedprogramme", filename)
        self.test_upload = os.path.join("/tmp", expected_upload)

        self.assertTrue(os.path.isfile(self.test_upload))

        # Check item was added:
        self.assertEqual(PrintedProgramme.objects.count(), 1)
        pp = PrintedProgramme.objects.all()[0]
        self.assertEqual(pp.month, date(2010, 4, 1))
        self.assertEqual(pp.designer, u"Designer nam\u0119")
        self.assertEqual(pp.notes, u"Blah blah no\u0167es")
        self.assertEqual(pp.programme.name, expected_upload)


class EditPrintedProgrammeTests(DiaryTestsMixin, TestCase):
    def setUp(self):
        super(EditPrintedProgrammeTests, self).setUp()
        self.client.login(username="admin", password="T3stPassword!")
        self.test_upload = None
        self._add_data()

    def tearDown(self):
        self.client.logout()
        try:
            if self.test_upload:
                os.unlink(self.test_upload)
        except OSError:
            pass

    def _write_pdf_magic(self, temp_pdf):
        temp_pdf.write('%PDF-1.3\r%\xe2\xe3\xcf\xd3\r\n')
        temp_pdf.seek(0)

    def _add_data(self):
        PrintedProgramme(
            month=date(2010, 6, 1),
            designer=u"Loop lop loop",
            programme=u"/foo/bar"
        ).save()
        PrintedProgramme(
            month=date(2010, 7, 1),
            designer=u"Can be yours for \u20ac10",
            programme=u"/what/bar/Nun"
        ).save()

    def test_edit_view_loads_no_data(self):
        PrintedProgramme.objects.all().delete()
        url = reverse("edit-printed-programmes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_view_loads_with_data(self):
        url = reverse("edit-printed-programmes")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"Loop lop loop")
        self.assertContains(response, u"Can be yours for \u20ac10")

    def test_edit_view_edit_data(self):
        url = reverse("edit-printed-programmes")
        response = self.client.post(url, data={
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MAX_NUM_FORMS": "1000",
            # "form-0-programme": "",
            "form-0-designer": u"Someon\u0113",
            "form-0-notes": u"",
            "form-0-id": "2",
            # "form-1-programme": "",
            # "form-1-designer": "Socks",
            "form-1-notes": u"Sm\u20aclt TERRIBLE",
            "form-1-id": "1",
        })
        self.assertRedirects(
            response,
            reverse("edit-printed-programmes")
        )
        # Check edits saved
        pp1 = PrintedProgramme.objects.get(pk=1)
        self.assertEqual(pp1.notes, u"Sm\u20aclt TERRIBLE")
        self.assertEqual(pp1.designer, u"")
        self.assertEqual(pp1.programme, u"/foo/bar")

        pp2 = PrintedProgramme.objects.get(pk=2)
        self.assertEqual(pp2.notes, u"")
        self.assertEqual(pp2.designer, u"Someon\u0113")
        self.assertEqual(pp2.programme, u"/what/bar/Nun")
