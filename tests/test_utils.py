from unittest import TestCase
import unittest.mock as mock
import Moog.utils as utils


class TestUpdateMock(TestCase):
    def test_args_are_parenthesized(self):
        par_args = utils.UpdateMockCommand.parenthesize_arguments
        self.assertEqual("", par_args(""))
        self.assertEqual("int a", par_args("int a"))
        self.assertEqual("int a, float b", par_args("int a, float b"))
        self.assertEqual("int a, std::string& b", par_args("int a, std::string& b"))
        self.assertEqual("int a, std::vector<int>& b", par_args("int a, std::vector<int>& b"))
        self.assertEqual("int a, (std::map<int, int>& b)", par_args("int a, std::map<int, int>& b"))
        self.assertEqual("int a, (std::map<int, int>& b), float* c", par_args("int a, std::map<int, int>& b, float* c"))
        self.assertEqual("int a, (std::map<int, std::map <float, float>>& b)", par_args("int a, std::map<int, std::map <float, float>>& b"))
