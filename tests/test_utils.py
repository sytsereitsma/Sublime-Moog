from unittest import TestCase
import unittest.mock as mock
import Moog.utils as utils


class TestUpdateMock(TestCase):
    def test_args_are_parenthesized(self):
        test_cases = [
            ("", ""),
            ("int a", "int a"),
            ("int a, float b", "int a, float b"),
            ("int a, std::string& b", "int a, std::string& b"),
            ("int a, std::vector<int>& b", "int a, std::vector<int>& b"),
            ("int a, (std::map<int, int>& b)", "int a, std::map<int, int>& b"),
            ("int a, (std::map<int, int>& b), float* c", "int a, std::map<int, int>& b, float* c"),
            ("int a, (std::map<int, std::map <float, float>>& b)", "int a, std::map<int, std::map <float, float>>& b"),
            ("int a, (std::map<int, std::map <float, float>>& b)", "int a, std::map<int, std::map <float, float>>& b"),
        ]

        parenthesize_arguments = utils.UpdateMockCommand.parenthesize_arguments
        for parenthesized, source in test_cases:
            self.assertEqual(parenthesized, parenthesize_arguments(source))

    def test_convert_mock(self):
        test_cases = [
            ("MOCK_METHOD (float, GetControllerFrequency, (), (const, override));", "MOCK_CONST_METHOD0(GetControllerFrequency, float());"),
            ("MOCK_METHOD (std::vector<KollmorgenDriver*>&, GetKollmorgenDrivers, (), (override));", "MOCK_METHOD0(GetKollmorgenDrivers, std::vector<KollmorgenDriver*>&());"),
        ]

        update_mock_method = utils.UpdateMockCommand.update_mock_method
        for converted, original in test_cases:
            self.assertEqual(converted, update_mock_method(original))
