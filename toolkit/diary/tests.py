"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
# from django.core.urlresolvers import reverse
from mock import patch


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class UrlTests(TestCase):
    @patch('toolkit.diary.views.view_diary')
    def test_diary_urls(self, view_mock):
        # Test all basic diary URLs

        calls_to_test = {
#                '/diary' : (), # This is a 302...
                '/diary/' : {},
                '/diary/2012' : {'year' : '2012',},
                '/diary/2012/' : {'year' : '2012',},
                '/diary/2012/12' : {'year' : '2012', 'month' : '12'},
                '/diary/2012/12/' : {'year' : '2012', 'month' : '12'},
                '/diary/2012/12/30' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                '/diary/2012/12/30/' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                }
        for query,response in calls_to_test.iteritems():
            self.client.get(query)
            self.assertTrue(view_mock.called)
            for k,v in response.iteritems():
                self.assertEqual(view_mock.call_args[1][k], v)
            view_mock.reset_mock()

    @patch('toolkit.diary.views.view_diary')
    def test_diary_invalid_urls(self, view_mock):
        # Test all basic diary URLs

        calls_to_test = (
                '/diary/123',
                '/diary/-123',
                '/diary/-2012/',
                '/diary/2012//',
                '/diary/2012///',
                )
        for query in calls_to_test:
            self.client.get(query)
            self.assertFalse(view_mock.called)

    @patch('toolkit.diary.views.edit_diary_list')
    def test_diary_edit_urls(self, view_mock):
        # Test all basic diary URLs

        calls_to_test = {
                '/diary/edit' : {},
                '/diary/edit/' : {},
                '/diary/edit/2012' : {'year' : '2012',},
                '/diary/edit/2012/' : {'year' : '2012',},
                '/diary/edit/2012/12' : {'year' : '2012', 'month' : '12'},
                '/diary/edit/2012/12/' : {'year' : '2012', 'month' : '12'},
                '/diary/edit/2012/12/30' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                '/diary/edit/2012/12/30/' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                }
        for query,response in calls_to_test.iteritems():
            self.client.get(query)
            self.assertTrue(view_mock.called)
            for k,v in response.iteritems():
                self.assertEqual(view_mock.call_args[1][k], v)
            view_mock.reset_mock()

    @patch('toolkit.diary.views.view_rota')
    def test_diary_rota_urls(self, view_mock):
        # Test all basic diary URLs

        calls_to_test = {
                '/diary/rota' : {},
                '/diary/rota/' : {},
                '/diary/rota/2012/12' : {'year' : '2012', 'month' : '12'},
                '/diary/rota/2012/12/' : {'year' : '2012', 'month' : '12'},
                '/diary/rota/2012/12/30' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                '/diary/rota/2012/12/30/' : {'year' : '2012', 'month' : '12', 'day' : '30'},
                '/diary/rota/2012/12//' : {'year' : '2012', 'month' : '12', 'day' : ''},
                }
        # (rota URLS must have at least year/month, not just a year!)
        for query,response in calls_to_test.iteritems():
            self.client.get(query)
            self.assertTrue(view_mock.called)
            for k,v in response.iteritems():
                self.assertEqual(view_mock.call_args[1][k], v)
            view_mock.reset_mock()

#class AuthTests(TestCase):
#    @patch('toolkit.diary.views.edit_diary_list')
#    @patch('toolkit.auth.views.auth')
#    def test_auth_required_views(self, auth_mock, edit_mock):
#        test_views = (
#                ('default-edit', {}),
#                ('month-edit', {'year':'1900','month':'12'}),
#                ('day-edit', {'year':'1900','month':'12', 'day':'1'}),
#                )
#        for view in test_views:
#            print view
#            reverse(view[0], kwargs=view[1])
##            request = self.client.get(url)
##            auth_mock.assert_called_once_with(request, 'read')
##
##            auth_mock.reset_mock()
##
#


