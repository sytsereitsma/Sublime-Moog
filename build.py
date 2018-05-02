import sublime
import sublime_plugin
import os
import glob
import subprocess
import threading


VS_VERSION = "VS2015"
MSBUILD = {
    "VS2015": r"C:\Program Files (x86)\MSBuild\14.0\Bin\amd64\MSBuild.exe"
}

#Copied from https://www.sublimetext.com/docs/3/build_systems.html#advanced_example
class MoogBuildCommand(sublime_plugin.WindowCommand):

    encoding = 'utf-8'
    killed = False
    proc = None
    panel = None
    panel_lock = threading.Lock()

    def is_enabled(self, lint=False, integration=False, kill=False):
        # The Cancel build option should only be available
        # when the process is still running
        if kill:
            return self.proc is not None and self.proc.poll() is None
        return True

    def log_in_panel(self, message):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': message})

    def get_project_file(self, filename, test):
        if test:
            project_file = _get_test_project(filename)
        else:
            project_file = _get_project(filename)

        if not project_file:
            self.log_in_panel("Cannot find project for '{}'\n".format(filename))
        else:
            self.log_in_panel("Building {}\n".format(os.path.basename(project_file)))

        return project_file

    def get_arguments(self, project_file, test):
        vs_version = "VS2015"
        args = ["cmd", "/C", MSBUILD[vs_version]]
        args.append(project_file)
        args.append('/p:Configuration=Debug')
        args.append('/maxcpucount')
        args.append('/v:q')  # Only log warnings and errors

        if test:
            project_dir = os.path.dirname(project_file)
            relative_root = project_dir
            if "Libs" in project_file:
                relative_root += "/../../../../"
            else:
                relative_root += "/../../../"
            relative_root += "Win32-bin-v14"

            root_dir = os.path.abspath(relative_root)

            project_name = os.path.basename(project_file)
            texter_exe = project_name.replace(".vcxproj", "D.exe")
            tester = os.path.join(root_dir, texter_exe)
            working_dir = os.path.abspath(project_dir + "/../..")
            args.append('&&')
            args.append('cd')
            args.append(working_dir)
            args.append('&&')
            args.append(tester)

        return args

    def run(self, test=False, kill=False):
        if kill:
            if self.proc:
                self.killed = True
                self.proc.terminate()
            return

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

            #"  c:\projects\head\libs\jsoncpp\src\src\lib_json\json_value.cpp(234): warning C4100: 'msg': unreferenced formal parameter [C:\Projects\HEAD\Libs\jsoncpp\bld\VS2015\jsoncpp.vcxproj]"
            settings.set(
                'result_file_regex',
                r'^\s+(.+)\((\d+)\):\s(.+)'
            )
            settings.set(
                'result_line_regex',
                r'^\s+line (\d+) col (\d+)'
            )

            self.window.run_command('show_panel', {'panel': 'output.exec'})

        if self.proc is not None:
            self.proc.terminate()
            self.proc = None

        vars = self.window.extract_variables()
        project_file = self.get_project_file(vars['file'], test)
        if not project_file:
            return

        args = self.get_arguments(project_file, test)

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
                self.queue_write(out.decode(self.encoding))
                if data == b'':
                    raise IOError('EOF')
                out = b''
            except (UnicodeDecodeError) as e:
                msg = 'Error decoding output using %s - %s'
                self.queue_write(msg % (self.encoding, str(e)))
                break
            except (IOError):
                if self.killed:
                    msg = 'Cancelled'
                else:
                    msg = 'Finished'
                self.queue_write('\n[%s]' % msg)
                break

    def queue_write(self, text):
        sublime.set_timeout(lambda: self.do_write(text.replace("\r", "")), 1)

    def do_write(self, text):
        with self.panel_lock:
            self.panel.run_command('append', {'characters': text})


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
