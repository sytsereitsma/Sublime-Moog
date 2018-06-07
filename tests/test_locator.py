import os
from unittest import TestCase
import unittest.mock as mock
from Moog.helpers import locator


class TestProjectLocator(TestCase):
    @mock.patch("Moog.helpers.locator.glob.glob")
    def test_get_vc_project(self, mock_glob):
        mock_glob.return_value = ["FooTester.vcxproj", "Foo.vcxproj"]
        project_file = locator.get_vc_project("Foo/src/bar.h")

        expected_glob = os.path.abspath("Foo/src\\..\\bld\\VS2015\\*.vcxproj")
        mock_glob.assert_called_once_with(expected_glob)
        self.assertEqual("Foo.vcxproj", project_file)

    @mock.patch("Moog.helpers.locator.glob.glob")
    @mock.patch("Moog.helpers.locator.os.path.isdir")
    def test_get_vc_project_vs2017(self, mock_isdir, mock_glob):
        mock_isdir.return_value = True

        mock_glob.return_value = ["FooTester.vcxproj", "Foo.vcxproj"]
        project_file = locator.get_vc_project("Foo/src/bar.h")

        expected_glob = os.path.abspath('Foo/src\\..\\bld\\VS2017\\*.vcxproj')
        mock_glob.assert_called_once_with(expected_glob)
        mock_isdir.assert_called_once_with("Foo/src\\..\\bld\\VS2017")

        self.assertEqual("Foo.vcxproj", project_file)

    @mock.patch("Moog.helpers.locator.glob.glob")
    def test_get_vc_test_project(self, mock_glob):
        mock_glob.return_value = ["FooTester.vcxproj", "Foo.vcxproj"]
        project_file = locator.get_vc_test_project("Foo/src/bar.h")
        self.assertEqual("FooTester.vcxproj", project_file)

    @mock.patch("Moog.helpers.locator.glob.glob", return_value=[])
    def test_get_vc_project_when_no_projects_are_found(self, _):
        self.assertIsNone(locator.get_vc_test_project("Foo/src/bar.h"))
        self.assertIsNone(locator.get_vc_project("Foo/src/bar.h",))

    def test_get_vc_test_project_for_fos_library(self):
        filename = "FoS/src/bar.h"
        dirname = os.path.dirname(filename)
        futil_tester = os.path.join(dirname,
                                    "..", "..", "Futil", "bld", "VS2015",
                                    "FutilLibTester.vcxproj")
        self.assertEqual(futil_tester,
                         locator.get_vc_test_project("FoS/src/bar.h"))

    def test_get_vc_project_for_smartestonelib_library(self):
        filename = "SmarTESTOneLib/src/bar.h"
        dirname = os.path.dirname(filename)
        project_dir = os.path.join(dirname,
                                   "..", "bld", "VS2015",
                                   "SmarTESTOneLib.vcxproj")

        self.assertEqual(project_dir, locator.get_vc_project(filename))

    @mock.patch("Moog.helpers.locator.glob.glob")
    def test_get_vc_project_for_tester_source_file_returns(self, mock_glob):
        # Should return test project
        mock_glob.return_value = ["FooTester.vcxproj", "Foo.vcxproj"]
        project_file = locator.get_vc_project("Foo/src/barTester.cpp")
        self.assertEqual("FooTester.vcxproj", project_file)

    def test_get_tester_and_working_dir_for_lib(self):
        tester, working_dir = locator.get_tester_and_working_dir(
            "Foo/Libs/Bar/bld/VS2015/Bar.vcxproj"
        )
        expected = os.path.abspath(os.path.join("Foo", "Win32-bin-v14", "BarD.exe"))
        self.assertEqual(expected, tester)

    def test_get_tester_and_working_dir_for_exe(self):
        tester, working_dir = locator.get_tester_and_working_dir(
            "Foo/Bar/bld/VS2015/Bar.vcxproj"
        )
        expected = os.path.abspath(os.path.join("Foo", "Win32-bin-v14", "BarD.exe"))
        self.assertEqual(expected, tester)

    def test_get_tester_and_working_dir_vs2017(self):
        tester, working_dir = locator.get_tester_and_working_dir(
            "Foo/Bar/bld/VS2017/Bar.vcxproj"
        )
        expected = os.path.abspath(os.path.join("Foo", "Win32-bin-v141", "BarD.exe"))
        self.assertEqual(expected, tester)
