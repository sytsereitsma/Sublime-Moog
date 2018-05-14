import glob
import os


def _get_project_files(filename, vs_project_dir):
    file_dir = os.path.dirname(filename)
    project_root = os.path.abspath(os.path.join(file_dir, ".."))
    bld_dir = os.path.join(project_root, "bld", vs_project_dir)
    project_files = glob.glob(os.path.join(bld_dir, "*.vcxproj"))

    return project_files


def get_vc_test_project(filename, vs_project_dir):
    if "fos" in filename.lower():
        dirname = os.path.dirname(filename)
        futil_tester = os.path.join(dirname,
                                    "../../Futil/bld/",
                                    vs_project_dir,
                                    "FutilLibTester.vcxproj")
        return futil_tester

    project_files = _get_project_files(filename, vs_project_dir)
    for project_file in project_files:
        if project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


def get_vc_project(filename, vs_project_dir):
    if filename.endswith("Tester.cpp"):
        return get_vc_test_project(filename, vs_project_dir)

    if "smartestonelib" in filename.lower():
        dirname = os.path.dirname(filename)
        smartestonelib_project = os.path.join(dirname,
                                              "../bld/",
                                              vs_project_dir,
                                              "SmarTESTOneLib.vcxproj")
        return smartestonelib_project

    project_files = _get_project_files(filename, vs_project_dir)
    for project_file in project_files:
        if not project_file.endswith("Tester.vcxproj"):
            return project_file
    return None


def get_tester_and_working_dir(project_file):
    project_dir = os.path.dirname(project_file)
    relative_root = project_dir
    if "libs" in project_file.lower():
        relative_root += "/../../../../"
    else:
        relative_root += "/../../../"
    relative_root += "Win32-bin-v14"

    root_dir = os.path.abspath(relative_root)

    project_name = os.path.basename(project_file)
    tester_exe = project_name.replace(".vcxproj", "D.exe")
    tester = os.path.join(root_dir, tester_exe)
    working_dir = os.path.abspath(project_dir + "/../../")

    return tester, working_dir
