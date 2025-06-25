import datetime

from mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from toolkit.members.models import TrainingRecord, Volunteer

from .common import MembersTestsMixin


class TestTrainingRecord(MembersTestsMixin, TestCase):
    def setUp(self):
        super(TestTrainingRecord, self).setUp()

    def test_clean_ok(self):
        record = TrainingRecord(
            training_type=TrainingRecord.GENERAL_TRAINING,
            volunteer=self.vol_1,
            role=None,
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=2, day=27),
        )
        record.clean()
        record.save()

    def test_clean_save_fail_no_type(self):
        record = TrainingRecord(
            training_type="",
            volunteer=self.vol_1,
            role=None,
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=2, day=27),
        )
        # not validated by clean() as forms will correctly validate this
        self.assertRaises(IntegrityError, record.save)

    def test_clean_save_fail_no_role(self):
        record = TrainingRecord(
            training_type=TrainingRecord.ROLE_TRAINING,
            volunteer=self.vol_1,
            role=None,
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=2, day=27),
        )
        self.assertRaises(ValidationError, record.clean)
        self.assertRaises(IntegrityError, record.save)

    def test_clean_save_fail_role_when_general(self):
        record = TrainingRecord(
            training_type=TrainingRecord.GENERAL_TRAINING,
            volunteer=self.vol_1,
            role=self.vol_1.roles.all()[0],
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=2, day=27),
        )
        self.assertRaises(ValidationError, record.clean)
        # This isn't (currently) enforced:
        record.save()

    @override_settings(DEFAULT_TRAINING_EXPIRY_MONTHS=6)
    @patch("toolkit.members.models.timezone_now")
    def test_has_expired_true(self, now_mock):

        now_mock.return_value.date.return_value = datetime.date(
            day=6, month=7, year=2010
        )

        record = TrainingRecord(
            training_type=TrainingRecord.GENERAL_TRAINING,
            volunteer=self.vol_1,
            role=None,
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=1, day=5),
        )
        self.assertTrue(record.has_expired())
        self.assertTrue(record.has_expired(expiry_age=0))
        self.assertFalse(record.has_expired(expiry_age=7))

    @override_settings(DEFAULT_TRAINING_EXPIRY_MONTHS=6)
    @patch("toolkit.members.models.timezone_now")
    def test_has_expired_false(self, now_mock):

        now_mock.return_value.date.return_value = datetime.date(
            day=6, month=7, year=2010
        )

        record = TrainingRecord(
            training_type=TrainingRecord.GENERAL_TRAINING,
            volunteer=self.vol_1,
            role=None,
            trainer="Nike Air Jordan",
            notes="A#",
            training_date=datetime.date(year=2010, month=1, day=6),
        )
        self.assertFalse(record.has_expired())


class TestVolunteerModel(MembersTestsMixin, TestCase):
    def test_latest_general_training_record_unsaved(self):
        v = Volunteer(member=self.mem_1)
        self.assertIsNone(v.latest_general_training_record())

    def test_latest_general_training_record_saved(self):
        self.assertIsNone(self.vol_1.latest_general_training_record())

        record = TrainingRecord(
            training_type=TrainingRecord.GENERAL_TRAINING,
            volunteer=self.vol_1,
            role=None,
            trainer="Adidas, I guess?",
            notes="440Hz",
            training_date=datetime.date(year=2020, month=4, day=20),
        )
        record.clean()
        record.save()

        self.assertEqual(record, self.vol_1.latest_general_training_record())
