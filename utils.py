import sublime
import sublime_plugin
import os

HEADER_TEMPLATE = """\
#ifndef {include_guard}
#define {include_guard}

{namespace_start}
class {class_name} {{
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

TEST_F({namespace_name}{class_name}Tester, Test) {{
    FAIL();
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
