import argparse
import os
import shutil
import hashlib
import subprocess
from threading import Thread
from multiprocessing import Pool
from datetime import datetime
from utils import generate_initramfs, generate_run_sh, mkdir,file_entrys, app_list
from configs import build_config, get_default_spec_list,get_spec_elf_list,def_config, prepare_config,get_default_spec_list,default_config,get_checkpoint_results
from simpoint import per_checkpoint_generate_worklist, per_checkpoint_generate_json, simpoint

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

def run_simpoint(spec_app):
    simpoint(def_config()["profiling_times"],def_config()["cluster_times"],def_config()["checkpoint_times"],spec_app)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Auto profiling and checkpointing")
    parser.add_argument('--elfs',help="Local spec programs folder (elf format)")
    parser.add_argument('--archive-folder',help="Archive folder name (default: archive)")
    parser.add_argument('--elf-suffix',help="Elf suffix in spec-bbl (default: _base.riscv64-linux-gnu-gcc12.2.0)")
    parser.add_argument('--spec-app-list',help="List of selected spec programs (default: all spec program)")
    parser.add_argument('--print-spec-app-list',action="store_true",help="Print default spec program list)")
    parser.add_argument('--message',help="Record info to the archive")
    parser.add_argument('--spec-bbl-checkpoint-mode',action='store_true',help="Generate spec bbl mode (set with before_workload,trap or not)")
    parser.add_argument('--profiling-times',help="Profiing times (default: 1; if set 0,you must set archive id and profiling id)")
    parser.add_argument('--cluster-times',help="Per profiling cluster times (default: 1; if set 0, you must set archive id and cluster id)")
    parser.add_argument('--checkpoint-times',help="Per cluster checkpoint times (default: 1; donot support set 0)")
    parser.add_argument('--profiling-id',help="Profiing start id (default: None)")
    parser.add_argument('--cluster-id',help="Cluster start id (default: None)")
    parser.add_argument('--checkpoint-id',help="Checkpoint id (default: None)")
    parser.add_argument('--archive-id',help="Archive id (default: use the md5 of the current time)")
    parser.add_argument('--max-threads',help="Max threads, must less then cpu nums (default: 10)")
    parser.add_argument('--build-bbl-only',action='store_true',help="Generate spec bbl only")

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

    init()
    assert(os.path.exists(def_config()["buffer"]))
    generate_archive_info(result_folder_md5,args.message)

    if args.archive_id==None:
        prepare_elf_buffer(args.elfs,def_config()["elf_suffix"])

    run_simpoint_args=[]
    #TODO: add multi thread support
    for spec in app_list(args.spec_app_list):
        if args.archive_id==None:
            prepare_rootfs(spec,args.spec_bbl_checkpoint_mode)
            build_spec_bbl(spec,def_config()["bin_suffix"])
        run_simpoint_args.append(spec)

    if args.build_bbl_only:
        exit(0)

    max_threads=10
    if args.max_threads!=None:
        max_threads=args.max_threads

    pool=Pool(processes=max_threads)
    pool.map_async(run_simpoint,run_simpoint_args)
    pool.close()
    pool.join()

    for result in get_checkpoint_results():
        per_checkpoint_generate_json(result["profiling_log"],result["cl_res"],app_list(args.spec_app_list),result["json_path"])
        per_checkpoint_generate_worklist(result["checkpoint_path"],result["list_path"])

        print("{}: {}".format("checkpoint path",result["checkpoint_path"]))
        print("{}: {}".format("json path",result["json_path"]))
        print("{}: {}".format("list path",result["list_path"]))



