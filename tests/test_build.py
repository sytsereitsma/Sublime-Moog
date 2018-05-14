from unittest import TestCase
import unittest.mock as mock
import Moog.build as build


class TestMoogBuildCommand(TestCase):
    def setUp(self):
        self.mock_window = mock.MagicMock()
        self.mock_panel = mock.MagicMock()
        self.command = build.MoogBuildCommand(self.mock_window)
        self.command.panel = self.mock_panel

    def assert_logged_in_panel(self, message):
        self.mock_panel.run_command.assert_called()
        panel_args, _ = self.mock_panel.run_command.call_args
        self.assertEqual("append", panel_args[0])
        self.assertEqual(message, panel_args[1]["characters"])

    @mock.patch("Moog.helpers.locator.get_vc_test_project")
    def test_get_project_file_for_test(self, mock_get_test_project):
        mock_get_test_project.return_value = "FooTester.vcxproj"
        self.assertEqual("FooTester.vcxproj",
                         self.command.get_project_file("foo.cpp", True))
        mock_get_test_project.assert_called_with("foo.cpp", "VS2015")

    @mock.patch("Moog.helpers.locator.get_vc_project")
    def test_get_project_file(self, mock_get_project):
        mock_get_project.return_value = "Foo.vcxproj"
        self.assertEqual("Foo.vcxproj",
                         self.command.get_project_file("foo.cpp", False))
        mock_get_project.assert_called_with("foo.cpp", "VS2015")

    @mock.patch("Moog.helpers.locator.get_vc_project", return_value="")
    def test_get_project_file_failure(self, _):
        self.assertIsNone(self.command.get_project_file("foo.cpp", False))
        self.assert_logged_in_panel("Cannot find project for 'foo.cpp'\n")

    @mock.patch("Moog.helpers.locator.get_vc_project",
                return_value="foo.vcxproj")
    def test_get_project_file_success_logs_build(self, _):
        self.command.get_project_file("foo.cpp", False)
        self.assert_logged_in_panel("Building foo.vcxproj\n")
