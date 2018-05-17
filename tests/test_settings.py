import os
from unittest import TestCase
import unittest.mock as mock
from Moog.helpers import settings
import imp

imp.reload(settings)


class TestSettings(TestCase):
    @mock.patch("Moog.helpers.settings.sublime.load_settings")
    def test_get_from_default(self, mock_load_settings):
        mock_settings = mock.MagicMock()
        mock_settings.get.return_value = "bar"
        mock_load_settings.return_value = mock_settings

        self.assertEqual("bar", settings.get("foo", "brrr"))
        mock_settings.get.assert_called_with("foo", "brrr")
        mock_load_settings.assert_called_with("Moog.sublime-settings")

    @mock.patch("Moog.helpers.settings.sublime.load_settings")
    @mock.patch("Moog.helpers.settings.sublime.active_window")
    def test_get_from_project(self, mock_active_window, mock_load_settings):
        mock_window = mock.MagicMock()
        mock_window.project_data.return_value = {"moog": {"foo": "yeah"}}
        mock_active_window.return_value = mock_window

        self.assertEqual("yeah", settings.get("foo", "brrr"))
        assert not mock_load_settings.called
