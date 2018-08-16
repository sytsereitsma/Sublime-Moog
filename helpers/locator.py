import glob
import os


def _get_vs_project_dir(root_dir, relative_bld_dir):
    bld_dir = os.path.join(root_dir, relative_bld_dir)
    vs2017_dir = os.path.join(bld_dir, "VS2017")
    if os.path.isdir(vs2017_dir) and glob.glob(os.path.join(vs2017_dir, "*.vcxproj")):
        return vs2017_dir

    return os.path.join(bld_dir, "VS2015")


def _get_project_files(filename):
    dirname = os.path.dirname(filename)
    project_dir = _get_vs_project_dir(dirname, os.path.join("..", "bld"))
    abs_project_dir = os.path.abspath(project_dir)
    project_files = glob.glob(os.path.join(abs_project_dir, "*.vcxproj"))
    return project_files


def get_vc_test_project(filename):
    if "fos" in filename.lower():
        dirname = os.path.dirname(filename)
        rel_dir = os.path.join("..", "..", "Futil", "bld")
        futil_tester = os.path.join(_get_vs_project_dir(dirname, rel_dir), "FutilLibTester.vcxproj")
        return futil_tester

    if "smartestonelib" in filename.lower():
        dirname = os.path.dirname(filename)
        rel_dir = os.path.join("..", "bld")

        smartestonelib_project = os.path.join(_get_vs_project_dir(dirname, rel_dir),
                                              "SmarTESTOneLibTester.vcxproj")
        return smartestonelib_project

    project_files = _get_project_files(filename)
    for project_file in project_files:
        if project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


def get_vc_project(filename):
    if filename.endswith("Tester.cpp"):
        return get_vc_test_project(filename)

    if "smartestonelib" in filename.lower():
        dirname = os.path.dirname(filename)
        rel_dir = os.path.join("..", "bld")
        smartestonelib_project = os.path.join(_get_vs_project_dir(dirname, rel_dir),
                                              "SmarTESTOneLib.vcxproj")
        return smartestonelib_project

    project_files = _get_project_files(filename)
    for project_file in project_files:
        if not project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


def get_tester_and_working_dir(project_file):
    project_dir = os.path.dirname(project_file)
    relative_root = project_dir
    if "libs" in project_file.lower():
        relative_root += os.path.join("..", "..", "..", "..", "..")
    else:
        relative_root += os.path.join("..", "..", "..", "..")

    if "2017" in project_file:
        relative_root += os.sep + "Win32-bin-v141"
    else:
        relative_root += os.sep + "Win32-bin-v14"

    root_dir = os.path.abspath(relative_root)

    project_name = os.path.basename(project_file)
    tester_exe = project_name.replace(".vcxproj", "D.exe")
    tester = os.path.join(root_dir, tester_exe)
    working_dir = os.path.abspath(project_dir + os.path.join("..", ".."))

    return tester, working_dir
