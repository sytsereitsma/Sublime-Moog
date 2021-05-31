import os
import re
import logging
import sublime
import sublime_plugin


HEADER_TEMPLATE = """\
#ifndef {include_guard}
#define {include_guard}

{namespace_start}
class {class_name} {{
public:
    {class_name} ();
    ~{class_name} ();
}};
{namespace_end}

#endif //{include_guard}
"""

SOURCE_TEMPLATE = """\
#include "{header_name}"


{namespace_start}
{class_name}::{class_name} () {{
}}

{class_name}::~{class_name} () {{
}}

{namespace_end}

"""

TESTER_TEMPLATE = """\
#include "gmock/gmock.h"
#include "{header_name}"

class {namespace_name}{class_name}Tester : public testing::Test {{
}};

TEST_F ({namespace_name}{class_name}Tester, Test) {{
    FAIL ();
}}
"""


class NewFileBase(sublime_plugin.WindowCommand):
    def get_name(self, prompt, callback):
        self.window.show_input_panel(prompt,
                                     "",
                                     callback,
                                     None, None)

    @classmethod
    def split_input_name(cls, input_name):
        if "::" in input_name:
            scope_index = input_name.index("::")
            namespace_name = input_name[:scope_index].strip()
            class_name = input_name[scope_index + 2:].strip()
        else:
            namespace_name = ""
            class_name = input_name

        return namespace_name, class_name

    @classmethod
    def base_name(cls, namespace_name, class_name):
        return namespace_name + class_name

    @classmethod
    def namespace_start(cls, namespace_name):
        if not namespace_name:
            return ""

        return "namespace " + namespace_name + " {\n"

    @classmethod
    def namespace_end(cls, namespace_name):
        if not namespace_name:
            return ""

        return "} // namespace " + namespace_name + "\n"

    def get_file_names(self, namespace_name, class_name):
        header_name = self.base_name(namespace_name, class_name) + ".h"
        source_name = self.base_name(namespace_name, class_name) + ".cpp"
        tester_name = self.base_name(namespace_name, class_name) + "Tester.cpp"

        return header_name, source_name, tester_name

    def write_and_open(self, filename, text):
        dir_name = os.path.dirname(self.window.active_view().file_name())
        file_path = os.path.join(dir_name, filename)
        open(file_path, "wt").write(text)

        self.window.open_file(file_path)

    def create_header(self, namespace_name, class_name):
        header_name, _, _ = self.get_file_names(namespace_name, class_name)
        include_guard = "_{}_{}_H_".format(namespace_name, class_name).upper()
        namespace_start = self.namespace_start(namespace_name)
        namespace_end = self.namespace_end(namespace_name)

        header_text = HEADER_TEMPLATE.format(include_guard=include_guard,
                                             namespace_start=namespace_start,
                                             namespace_end=namespace_end,
                                             class_name=class_name)

        self.write_and_open(header_name, header_text)

    def create_source(self, namespace_name, class_name):
        header_name, source_name, _ = self.get_file_names(namespace_name,
                                                          class_name)
        namespace_start = self.namespace_start(namespace_name)
        namespace_end = self.namespace_end(namespace_name)

        source_text = SOURCE_TEMPLATE.format(header_name=header_name,
                                             namespace_start=namespace_start,
                                             namespace_end=namespace_end,
                                             class_name=class_name)

        self.write_and_open(source_name, source_text)

    def create_tester(self, namespace_name, class_name):
        header_name, _, tester_name = self.get_file_names(namespace_name,
                                                          class_name)

        source_text = TESTER_TEMPLATE.format(header_name=header_name,
                                             namespace_name=namespace_name,
                                             class_name=class_name)

        self.write_and_open(tester_name, source_text)


class NewClassCommand(NewFileBase):
    def run(self):
        prompt = "Class name (prepend namespace if any, e.g.: Foo::Bar)"
        self.get_name(prompt, self.create_and_open)

    def create_and_open(self, input_name: str) -> None:
        input_name = input_name.strip()
        if not input_name:
            return

        namespace_name, class_name = self.split_input_name(input_name)

        self.create_header(namespace_name, class_name)
        self.create_source(namespace_name, class_name)
        self.create_tester(namespace_name, class_name)


class NewTesterCommand(NewFileBase):
    def run(self):
        prompt = "Class name to test"
        prompt += "(prepend namespace if any, e.g.: Foo::Bar)"
        self.get_name(prompt, self.create_and_open)

    def create_and_open(self, input_name: str) -> None:
        input_name = input_name.strip()
        if not input_name:
            return

        namespace_name, class_name = self.split_input_name(input_name)

        tester_suffix = "Tester"
        if class_name.endswith(tester_suffix):
            class_name = class_name[:-len(tester_suffix)]

        self.create_tester(namespace_name, class_name)


class NewHeaderCommand(NewFileBase):
    def run(self):
        prompt = "Header file name"
        self.get_name(prompt, self.create_and_open)

    def create_and_open(self, input_name: str) -> None:
        input_name = input_name.strip()
        if not input_name:
            return

        if ".h" in input_name:
            class_name = input_name[:-2]
        else:
            class_name = input_name

        self.create_header("", class_name)


class UpdateMockCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.replace_next_mock(edit, sublime.Region(0, 1))
        prev_end = -1
        while region is not None and prev_end < region.a:
            prev_end = region.b
            region = self.replace_next_mock(edit, region)

    def replace_next_mock(self, edit, region):
        start_mock = self.view.find(r"MOCK_(CONST_)?METHOD\d*", region.a)
        if start_mock is not None:
            end_mock = self.view.find(";", start_mock.b)
            if end_mock is not None:
                self.update_mock_method(edit, sublime.Region(start_mock.a, end_mock.b))
                return sublime.Region(end_mock.b, end_mock.b + 1)

        return None

    @staticmethod
    def cleanup_declaration(mock_declaration):
        mock_declaration = mock_declaration.replace("\n", "")
        mock_declaration = mock_declaration.replace("\r", "")
        mock_declaration = re.sub(r"\s+", " ", mock_declaration)

        return mock_declaration

    @staticmethod
    def parenthesize_arguments(arguments):
        args = arguments.split(",")
        parenthesized = []
        this_arg = ""

        def append_this_arg(arg):
            parenthesized.append(arg.strip())
            return ""

        lt_count = 0  # '<' count (nested templates)
        for a in args:
            if lt_count == 0 and "<" in a and ">" not in a:
                this_arg += "(" + a.strip()
                lt_count += 1
            else:
                if this_arg:
                    this_arg += ", "

                this_arg += a.strip()
                if lt_count != 0 and ">" in a:
                    lt_count -= 1
                    if lt_count == 0:
                        this_arg += ")"
                        this_arg = append_this_arg(this_arg)
                else:
                    this_arg = append_this_arg(this_arg)

        if this_arg:
            append_this_arg(this_arg)

        return ", ".join(parenthesized)

    def update_mock_method(self, edit, region):
        mock_declaration = self.cleanup_declaration(self.view.substr(region))

        pattern = r".+\("
        pattern += r"([A-Za-z0-9_]+)\s*"  # function name
        pattern += r"\s*,\s*"
        pattern += r"([A-Za-z0-9_:&\*\s]+)\("  # function return type
        pattern += r"(.*)\s*\)\s*\);"  # function arguments

        m = re.match(pattern, mock_declaration)
        if m is not None:
            name = m.group(1)
            ret = m.group(2)
            args = self.parenthesize_arguments(m.group(3))
            qualifiers = "const, override" if "_CONST_" in mock_declaration else "override"
            replacement_mock = "MOCK_METHOD ({}, {}, ({}), ({}));".format(
                ret.strip(), name.strip(), args.strip(), qualifiers.strip())
            self.view.replace(edit, region, replacement_mock)


class StandardizeCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        super(StandardizeCommand, self).__init__(view)
        classes = "|".join([
            "string",
            "string_view",
            r"vector\s*<",
            r"map\s*<",
            r"list\s*<",
            r"set\s*<",
            r"pair\s*<",
            "endl",
            "fstream",
            "ifstream",
            "ofstream",
            "unique_ptr",
            "shared_ptr",
        ])

        self._std_re = re.compile(
            r"(?<!std::)\b(" + classes + r")\b(.+[;{])"
        )

    def run(self, edit):
        region = self.process_next_line(edit, sublime.Region(0, 1))
        count = 0
        while region is not None and region.a < self.view.size():
            region = self.process_next_line(edit, region)

            count += 1
            if count > 1000:
                logging.error("whoops {}, {}".format(region.a, region.b))
                break

    def process_next_line(self, edit, region):
        region = self.view.full_line(region)
        org_line = self.view.substr(region)
        line = self._std_re.sub(r"std::\1\2", org_line)
        if line != org_line:
            logging.info("< " + org_line.strip())
            logging.info("> " + line.strip())

        self.view.replace(edit, region, line)
        return sublime.Region(region.b + 1, region.b + 2)


class FooCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = sublime.load_settings("Moog.sublime-settings")
        logging.error(self.window.project_data())
