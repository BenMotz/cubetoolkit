import os.path
import tempfile

from mock import patch

from django.test import TestCase

import toolkit.util.image as image

TINY_PNG = ('\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00' +
           '\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03sBIT\x08\x08' +
           '\x08\xdb\xe1O\xe0\x00\x00\x00\x06PLTE\xff\xff\xff\x00\x00\x00U' +
           '\xc2\xd3~\x00\x00\x00\x02tRNS\xff\x00\xe5\xb70J\x00\x00\x00\tpHY' +
           's\x00\x00\r:\x00\x00\r:\x01\x03"\x1e\x85\x00\x00\x00\nIDAT\x08' +
           '\x99c\x90\x01\x00\x00\x1e\x00\x1dZn\x8b\x81\x00\x00\x00\x00IEND' +
           '\xaeB`\x82')

class ThumbnailerTests(TestCase):

    @patch("toolkit.util.image.get_mimetype")
    def test_gen_thumbnail_text_file(self, get_mimetype_patch):
        """Test handling of non-image file"""
        get_mimetype_patch.return_value = "text/plain"

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".jpg") as temp_jpg:
            temp_jpg.write("Not an empty jpeg")
            temp_jpg.seek(0)

            file_name = temp_jpg.name
            thumb_name = file_name + ".thumb"

            self.assertRaisesMessage(
                image.ThumbnailError,
                u"Creating thumbnails for non-image files not supported at this time",
                image.generate_thumbnail, temp_jpg, thumb_name, (50, 50)
            )

            get_mimetype_patch.assert_called_once_with(temp_jpg)

    def test_gen_thumbnail_jpeg_from_png(self):
        """Generate a thumbnail from 1x1 PNG"""
        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".png") as temp_png:
            temp_png.write(TINY_PNG)
            temp_png.seek(0)

            file_name = temp_png.name
            thumb_name = file_name + ".thumb"

            actual_thumb_name = image.generate_thumbnail(temp_png, thumb_name, (50, 50))

            # Check created file:
            self.assertTrue(os.path.isfile(actual_thumb_name))
            with open(actual_thumb_name, "rb") as thumb_file:
                self.assertEqual(
                    image.get_mimetype(thumb_file),
                    "image/jpeg"
                )
            # Delete thumbnail:
            os.unlink(actual_thumb_name)

    def test_gen_thumbnail_jpeg_from_png_overwrite(self):
        """Test thumbnail from 1x1 PNG when dest already exists"""

        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".png") as temp_png:
            with tempfile.NamedTemporaryFile(dir="/tmp", prefix="toolkit-test-", suffix=".jpg") as temp_jpg:
                temp_png.write(TINY_PNG)
                temp_png.seek(0)

                thumb_name = temp_jpg.name

                actual_thumb_name = image.generate_thumbnail(temp_png, thumb_name, (50, 50))

                self.assertEqual(actual_thumb_name, thumb_name)

                # Check created file:
                self.assertTrue(os.path.isfile(actual_thumb_name))
                with open(actual_thumb_name, "rb") as thumb_file:
                    self.assertEqual(
                        image.get_mimetype(thumb_file),
                        "image/jpeg"
                    )
