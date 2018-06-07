import sublime
import sublime_plugin
import os
import subprocess
import threading
from .helpers import locator

# todo: MAke these settings
MSBUILD = {
    "VS2015": r"C:\Program Files (x86)\MSBuild\14.0\Bin\amd64\MSBuild.exe",
    "VS2017": r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"
}


class PanelWriter:
    def __init__(self, panel):
        self.lock = threading.Lock()
        self.panel = panel

    def write(self, message):
        with self.lock:
            self.panel.run_command('append',
                                   {'characters': message.replace("r", "")})


# Copied from https://www.sublimetext.com/docs/3/build_systems.html#advanced_example # noqa
class MoogBuildCommand(sublime_plugin.WindowCommand):
    encoding = 'utf-8'
    killed = False
    proc = None
    panel_lock = threading.Lock()
    panel = None
    test_args = "--gtest_filter=*"

    def is_enabled(self, lint=False, integration=False, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    def get_project_file(self, filename, test):
        if test:
            project_file = locator.get_vc_test_project(filename)
        else:
            project_file = locator.get_vc_project(filename)

        if not project_file:
            self.write_to_panel("Cannot find project for '{}'\n"
                                .format(filename))
            project_file = None
        else:
            self.write_to_panel("Building {}\n"
                                .format(os.path.basename(project_file)))

        return project_file

    def get_arguments(self, filename, test, compile_):
        project_file = self.get_project_file(filename, test)
        if not project_file:
            return None

        vs_version = "VS2015" if "VS2015" in project_file else "VS2017"
        args = ["cmd", "/C", MSBUILD[vs_version]]
        args.extend([
            project_file,
            '/p:Configuration=Debug',
            '/maxcpucount',
            '/v:q'  # q, only warnings and errors
        ])

        if compile_:
            args.append('/t:ClCompile')
            args.append('/p:SelectedFile={}'
                        .format(os.path.basename(filename)))
        elif test:
            tester, working_dir = \
                locator.get_tester_and_working_dir(project_file)
            args.extend([
                '&&', 'cd', working_dir, '&&', tester, self.test_args
            ])

            self.write_to_panel("Tester {}\n"
                                "Test arguments {}\n"
                                .format(tester, self.test_args))

        return args

    def run_test(self, test_args: str) -> None:
        self.test_args = test_args
        self.run_impl(True, False)

    def run(self, test=False, kill=False, compile_=False):
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return

        if test:
            self.window.show_input_panel("Test arguments",
                                         self.test_args,
                                         self.run_test,
                                         None, None)
        else:
            self.run_impl(False, compile_)

    def run_impl(self, test=False, compile_=False):
        self.create_output_panel()

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        filename = self.window.active_view().file_name()
        args = self.get_arguments(filename, test, compile_)
        if not args:
            return

        project_file = self.get_project_file(filename, test)
        self.proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(project_file)
        )
        self.killed = False

        threading.Thread(
            target=self.read_handle,
            args=(self.proc.stdout,)
        ).start()

    def create_output_panel(self):
        # A lock is used to ensure only one thread is
        # touching the output panel at a time
        with self.panel_lock:
            # Creating the panel implicitly clears any previous contents
            self.panel = self.window.create_output_panel('exec')

            # Enable result navigation. The result_file_regex does
            # the primary matching, but result_line_regex is used
            # when build output includes some entries that only
            # contain line/column info beneath a previous line
            # listing the file info. The result_base_dir sets the
            # path to resolve relative file names against.
            settings = self.panel.settings()

            #  ...\foo.cpp(234): warning C4100: bar message
            settings.set(
                'result_file_regex',
                r'^\s*(.+)\((\d+)\):\s(.+)'
            )
            settings.set(
                'result_line_regex',
                r'^\s+line (\d+) col (\d+)'
            )

            self.window.run_command('show_panel', {'panel': 'output.exec'})

    def read_handle(self, handle):
        chunk_size = 2 ** 13
        out = b''
        while True:
            try:
                data = os.read(handle.fileno(), chunk_size)
                # If exactly the requested number of bytes was
                # read, there may be more data, and the current
                # data may contain part of a multibyte char
                out += data
                if len(data) == chunk_size:
                    continue
                if data == b'' and out == b'':
                    raise IOError('EOF')
                # We pass out to a function to ensure the
                # timeout gets the value of out right now,
                # rather than a future (mutated) version
                self.async_write_to_panel(out.decode(self.encoding))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.async_write_to_panel(msg % (self.encoding, str(e)))
                break
            except (IOError):
                if self.killed:
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                self.async_write_to_panel('\n[%s]' % msg)
                break

    def async_write_to_panel(self, text):
        sublime.set_timeout(lambda: self.write_to_panel(text.replace("\r", "")), 1)

    def write_to_panel(self, text):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})
