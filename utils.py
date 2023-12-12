import os
import pathlib
from configs import default_initramfs_file, def_config, get_default_spec_list, prepare_config
from configs import get_spec_info


# exists will raise exception, exception will broke pool
def mkdir(path):
    try:
        if not pathlib.Path(path).exists():
            os.makedirs(path)
    except:
        pass

def entrys(path):
    entrys_list = []
    with os.scandir(path) as el:
        for entry in el:
            entrys_list.append(entry)
    return entrys_list


def file_entrys(path):
    file_list = []
    for entry in entrys(path):
        if entry.is_file:
            file_list.append(entry)
    return file_list


def absp(path):
    if os.path.exists(path):
        return os.path.abspath(path)
    else:
        raise


def traverse_path(path, stack=""):
    all_dirs, all_files = [], []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        item_stack = os.path.join(stack, item)
        if os.path.isfile(item_path):
            all_files.append(item_stack)
        else:
            all_dirs.append(item_stack)
            sub_dirs, sub_files = traverse_path(item_path, item_stack)
            all_dirs.extend(sub_dirs)
            all_files.extend(sub_files)
    return (all_dirs, all_files)


def generate_initramfs(specs, elf_suffix, dest_path):
    lines = default_initramfs_file.copy()
    for spec in specs:
        spec_files = get_spec_info(def_config()["cpu2006_run_dir"],
                                   prepare_config()["elf_folder"],
                                   elf_suffix)[spec][0]
        for i, filename in enumerate(spec_files):
            if len(filename.split()) == 1:
                # print(f"default {filename} to file 755 0 0")
                basename = filename.split("/")[-1]
                filename = f"file /spec/{basename} {filename} 755 0 0"
                lines.append(filename)
            elif len(filename.split()) == 3:
                node_type, name, path = filename.split()
                if node_type != "dir":
                    print(f"unknown filename: {filename}")
                    continue
                all_dirs, all_files = traverse_path(path)
                lines.append(f"dir /spec/{name} 755 0 0")
                for sub_dir in all_dirs:
                    lines.append(f"dir /spec/{name}/{sub_dir} 755 0 0")
                for file in all_files:
                    lines.append(
                        f"file /spec/{name}/{file} {path}/{file} 755 0 0")
            else:
                print(f"unknown filename: {filename}")
    with open(os.path.join(dest_path, "initramfs-spec.txt"), "w") as f:
        f.writelines(map(lambda x: x + "\n", lines))


def generate_run_sh(specs, elf_suffix, dest_path, withTrap=False):
    lines = []
    lines.append("#!/bin/sh")
    lines.append("echo '===== Start running SPEC2006 ====='")
    for spec in specs:
        spec_bin = get_spec_info(def_config()["cpu2006_run_dir"],
                                 prepare_config()["elf_folder"],
                                 elf_suffix)[spec][0][0].split("/")[-1]
        spec_cmd = " ".join(
            get_spec_info(def_config()["cpu2006_run_dir"],
                          prepare_config()["elf_folder"], elf_suffix)[spec][1])
        lines.append(f"echo '======== BEGIN {spec} ========'")
        lines.append("set -x")
        lines.append(f"md5sum /spec/{spec_bin}")
        lines.append("date -R")
        if withTrap:
            lines.append("/spec_common/before_workload")

        if spec=="xalancbmk":
            lines.append(f"cd /spec && ./{spec_bin} {spec_cmd} > xalan.out")
        else:
            lines.append(f"cd /spec && ./{spec_bin} {spec_cmd}")
        lines.append("ls /spec")

        if withTrap:
            lines.append("/spec_common/trap")
        lines.append("date -R")
        lines.append("set +x")
        lines.append(f"echo '======== END   {spec} ========'")
    lines.append("echo '===== Finish running SPEC2006 ====='")
    with open(os.path.join(dest_path, "run.sh"), "w") as f:
        f.writelines(map(lambda x: x + "\n", lines))


def app_list(list_path,app_list):
    if list_path == None and app_list == None:
        return get_default_spec_list()
    elif list_path == None and app_list != None:
        apps=app_list.split(',')
        return list(set(apps))
    else:
        app_list = []
        with open(list_path) as l:
            app_list = l.read().splitlines()
        return list(set(app_list))

