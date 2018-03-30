import sublime
import sublime_plugin
import os
import glob

VS_VERSION = "VS2015"


def _get_project_files(filename):
    file_dir = os.path.dirname(filename)
    project_root = os.path.abspath(os.path.join(file_dir, ".."))
    bld_dir = os.path.join(project_root, "bld", VS_VERSION)
    if os.path.isdir(bld_dir):
        return glob.glob(os.path.join(bld_dir, "*.vcxproj"))

    return []


def _get_test_project(filename):
    project_files = _get_project_files(filename)
    for project_file in project_files:
        if project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


def _get_project(filename):
    project_files = _get_project_files(filename)
    for project_file in project_files:
        if not project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


class CompileCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # "/t:ClCompile "p:/SelectedFiles="main.cpp"
        self.view.insert(edit, 0, _get_project(self.view.file_name()))


class TestProjectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.insert(edit, 0, _get_test_project(self.view.file_name()))
