import logging
import os
import subprocess
import sublime_plugin


class ClangTidyCommand(sublime_plugin.WindowCommand):
    previous_command = "--fix-errors -checks=-*,modernize-use-override,modernize-replace-auto-ptr"

    def run(self):
        self.window.show_input_panel("Arguments",
                                     ClangTidyCommand.previous_command,
                                     self.run_clang_tidy,
                                     None, None)

    def run_clang_tidy(self, cmd: str):
        ClangTidyCommand.previous_command = cmd

        flags = None
        root_dir = self.get_root_dir()
        if root_dir is not None:
            flags = self.get_clang_complete_flags(root_dir)

        if flags is not None:
            relative_path = os.path.relpath(
                self.window.active_view().file_name(), root_dir)
            args = ["clang-tidy.exe"]
            args += cmd.split(" ")
            args.append(relative_path)
            args.append("--")
            args += flags

            try:
                output = subprocess.check_output(
                    args,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    cwd=root_dir)
                logging.info(output.decode())
            except subprocess.CalledProcessError as e:
                output = e.output.decode()
                if "error: invalid argument '-std=c++17' not allowed with 'C' [clang-diagnostic-error]" not in output:
                    logging.error(output)

    def get_root_dir(self):
        filename = self.window.active_view().file_name()
        root_dir = None
        for folder in self.window.folders():
            if os.path.commonprefix([filename, folder]) == folder:
                root_dir = folder
                break

        if root_dir is None:
            logging.error("Could not find project root dir of " + filename)
            return None

        return root_dir

    def get_clang_complete_flags(self, root_dir):
        clang_complete_file = os.path.join(root_dir, ".clang_complete")
        if not os.path.exists(clang_complete_file):
            logging.error("Could not find clang compile commands file " + clang_complete_file)
            return None

        def process_flag(flag):
            flag = flag.strip()
            return flag

        flags = ["-std=c++17"]
        flags += list(map(process_flag, open(clang_complete_file)))

        return flags
