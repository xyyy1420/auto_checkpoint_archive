import argparse
import os
import shutil
import hashlib
import subprocess
from threading import Thread
from datetime import datetime
from utils import generate_initramfs, generate_run_sh, mkdir,file_entrys, app_list
from configs import build_config, get_default_spec_list, get_spec_elf_list,def_config, prepare_config,get_default_spec_list,default_config
from simpoint import simpoint

def generate_archive_info(md5,message):
    with open(os.path.join(def_config()["archive_folder"],"archive_info"),"a") as f:
        f.write(f"{md5}: {message}\n")

def init():
    for value in build_config().values():
        mkdir(value)
    for value in prepare_config().values():
        mkdir(value)

def gen_copy_list_item(src_name,src_path,append_elf_suffix=def_config()["elf_suffix"]):
    target_path=""
    for program in get_spec_elf_list():
        if src_name.find(program) != -1:
            target_path=os.path.join(prepare_config()["elf_folder"],program+append_elf_suffix)
            return ([src_path,target_path])
    else:
        return []

def prepare_elf_buffer(source_elf_path,append_elf_suffix):
    prepare_copy_list=[]
    copy_threads=[]

    for entry in file_entrys(source_elf_path):
        item=gen_copy_list_item(entry.name,entry.path,append_elf_suffix)
        if item != []:
            prepare_copy_list.append(item)
            thread=Thread(target=shutil.copy,args=item)
            thread.start()
            copy_threads.append(thread)

    for thread in copy_threads:
        thread.join()

def build_spec_bbl(spec,bin_suffix):

    print(f"build {spec}-bbl-linux-spec...")

    with open(os.path.join(build_config()["build_log"],f"build-{spec}-out.log"),"w") as out,open(os.path.join(build_config()["build_log"],f"build-{spec}-err.log"),"w") as err:
        res=subprocess.run(["make","clean"],cwd=def_config()["pk"],stdout=out,stderr=err)
        res.check_returncode()
        res=subprocess.run(["make","-j70"],cwd=def_config()["pk"],stdout=out,stderr=err)
        res.check_returncode()

    target_file=os.path.join(def_config()["pk"],"build","bbl.bin")
    cp_dest=os.path.join(build_config()["bin_folder"],f"{spec}{bin_suffix}")
    shutil.copy(target_file,cp_dest)

def prepare_rootfs(spec,withTrap=True):
    generate_initramfs([spec],def_config()["elf_suffix"],def_config()["riscv-rootfs"])
    generate_run_sh([spec],def_config()["elf_suffix"],def_config()["riscv-rootfs"],withTrap)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Using for auto profiling and checkpoint")
    parser.add_argument('--elfs',help="Spec programs folder")
    parser.add_argument('--archive-folder',help="Save all result (default: archive)")
    parser.add_argument('--elf-suffix',help="Elf suffix (default: _base.riscv64-linux-gnu-gcc12.2.0)")
    parser.add_argument('--spec-app-list',help="Selected spec programs (default: all spec program)")
    parser.add_argument('--print-spec-app-list',action="store_true",help="Print defaul spec program list)")
    parser.add_argument('--message',help="Message flags result,just like git commit message")
    parser.add_argument('--checkpoints',action='store_true',help="Checkpoints mode (with before_workload and trap)")
    parser.add_argument('--profiling-times',help="Profiing times (default: 1; if set 0,you must set archive id and profiling id)")
    parser.add_argument('--cluster-times',help="Per profiling cluster times (default: 1; if set 0, you must set archive id and cluster id)")
    parser.add_argument('--checkpoint-times',help="Per cluster checkpoint times (default: 1)")
    parser.add_argument('--profiling-id',help="Profiing start id (default: 0)")
    parser.add_argument('--cluster-id',help="Cluster start id (default: 0)")
    parser.add_argument('--checkpoint-id',help="Checkpoint times (default: 0)")
    parser.add_argument('--archive-id',help="Archive id (default: auto generate)")

    args=parser.parse_args()

    if args.print_spec_app_list:
        print(get_default_spec_list())
        exit(0)

    # set user profiling, cluster, checkpoint times
    if args.profiling_times!=None:
        default_config["profiling_times"]=int(args.profiling_times)
    if args.cluster_times!=None:
        default_config["cluster_times"]=int(args.cluster_times)
    if args.checkpoint_times!=None:
        default_config["checkpoint_times"]=int(args.checkpoint_times)

    # TODO: fix this pending bug, just make checkpoint times >= cluster times ? or ensure cluster is exist
    if def_config()["profiling_times"]<=def_config()["cluster_times"] and def_config()["cluster_times"]<=def_config()["checkpoint_times"]:
        pass
    else:
        print("You must ensure profiling times <= cluster times <= checkpoint times")
        exit(1)

    if def_config()["profiling_times"]==0 and (args.archive_id==None or args.profiling_id==None):
        print("When set profiling times 0, you must set archive id and profiling id")
        exit(1)
    else:
        default_config["profiling_id"]=args.profiling_id

    if def_config()["cluster_times"]==0 and (args.archive_id==None or args.cluster_id==None):
        print("When set cluster times 0, you must set archive id and cluster id")
        exit(1)
    else:
        default_config["cluster_id"]=args.cluster_id

    # user set elf suffix
    if args.elf_suffix != None:
        default_config["elf_suffix"]=args.elf_suffix

    # user set archive folder
    if args.archive_folder != None:
        default_config["archive_folder"]=args.archive_folder

    # record user message
    if args.message == None:
        print("Without message might could not find profiling result")
        args.message="No message"

    # calculate result md5
    result_folder_md5=hashlib.md5(datetime.now().strftime("%Y-%m-%d-%H-%M").encode("utf-8")).hexdigest()

    if args.archive_id!=None:
        result_folder_md5=args.archive_id

    default_config["buffer"]=os.path.join(default_config["archive_folder"],str(result_folder_md5))
    assert(os.path.exists(def_config()["buffer"]))

    init()
    generate_archive_info(result_folder_md5,args.message)

    if args.archive_id==None:
        prepare_elf_buffer(args.elfs,def_config()["elf_suffix"])

    for spec in app_list(args.spec_app_list):
        if args.archive_id==None:
            prepare_rootfs(spec,args.checkpoints)
            build_spec_bbl(spec,def_config()["bin_suffix"])

        simpoint(def_config()["profiling_times"],def_config()["cluster_times"],def_config()["checkpoint_times"],spec)

