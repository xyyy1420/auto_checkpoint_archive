import os
import subprocess
from configs import def_config, simpoint_config
from configs import profiling_command, cluster_command, checkpoint_command, append_checkpoint_result, qemu_profiling_command, qemu_checkpoint_command
from utils import mkdir
import json
import re
import threading


def profiling(workload, ptime):
    #    pres_folder=os.path.join(def_config()["buffer"],simpoint_config()["profiling_folder"].format(ptime))
    pres_folder = os.path.join(
        simpoint_config()["profiling_folder"].format(ptime))
    #    mkdir(pres_folder)

    profiling_out = os.path.join(
        simpoint_config()["profiling_logs"].format(ptime),
        "{}-out.log".format(workload))
    profiling_err = os.path.join(
        simpoint_config()["profiling_logs"].format(ptime),
        "{}-err.log".format(workload))

    mkdir(os.path.split(profiling_out)[0])

    print("Profiling, workload: {}, times: {}, output path: {}, err path: {}".format(workload,ptime,profiling_out,profiling_err))
    with open(profiling_out, "w") as out, open(profiling_err, "w") as err:
        if def_config()["emulator"]=="NEMU":
            command=profiling_command(workload, pres_folder)
        else:
            command=qemu_profiling_command(workload, pres_folder)
        print(command)
        res = subprocess.run(command,
                             stdout=out,
                             stderr=err)
# if use normal "trap", check_returncode will return, else check_return will raise err, we use qemu_trap, so comment this for now
        res.check_returncode()


def cluster(workload, ptime, cltime):
    pres_folder = os.path.join(
        def_config()["buffer"],
        simpoint_config()["profiling_folder"].format(ptime))
    cl_res_folder = os.path.join(
        def_config()["buffer"],
        simpoint_config()["cluster_folder"].format(ptime, cltime), workload)
    mkdir(cl_res_folder)

    cluster_out = os.path.join(
        simpoint_config()["cluster_logs"].format(ptime, cltime),
        "{}-out.log".format(workload))
    cluster_err = os.path.join(
        simpoint_config()["cluster_logs"].format(ptime, cltime),
        "{}-err.log".format(workload))

    mkdir(os.path.split(cluster_out)[0])
    print("Cluster, workload: {}, using profiling result: {}, cluster id: {}, output path: {}, err path: {}".format(workload,ptime,cltime,cluster_out,cluster_err))

    with open(cluster_out, "w") as out, open(cluster_err, "w") as err:
        res = subprocess.run(cluster_command(workload, pres_folder,
                                             cl_res_folder),
                             stdout=out,
                             stderr=err)

        res.check_returncode()


def checkpoint(workload, ptime, cltime, ctime):
    cl_res_folder = os.path.join(
        def_config()["buffer"],
        simpoint_config()["cluster_folder"].format(ptime, cltime))

    cres_folder = os.path.join(simpoint_config()["checkpoint_folder"].format(
        ptime, cltime, ctime))

    checkpoint_out = os.path.join(
        simpoint_config()["checkpoint_logs"].format(ptime, cltime, ctime),
        "{}-out.log".format(workload))
    checkpoint_err = os.path.join(
        simpoint_config()["checkpoint_logs"].format(ptime, cltime, ctime),
        "{}-err.log".format(workload))

    mkdir(os.path.split(checkpoint_out)[0])

    print("Checkpointing, workload: {}, using profiling result: {}, using cluster result: {}, checkpoint id: {}, output path: {}, err path: {}".format(workload,ptime,cltime,ctime,checkpoint_out,checkpoint_err))

    with open(checkpoint_out, "w") as out, open(checkpoint_err, "w") as err:
        if def_config()["emulator"]=="NEMU":
            command=checkpoint_command(workload, cl_res_folder,
                                                cres_folder)
        else:
            command=qemu_checkpoint_command(workload, cl_res_folder,
                                                cres_folder)

        print(command)
        res = subprocess.run(command,
                             stdout=out,
                             stderr=err)

        res.check_returncode()

    result = {
        "cl_res":
        os.path.join(cl_res_folder),
        "profiling_log":
        os.path.join(simpoint_config()["profiling_logs"].format(ptime)),
        "checkpoint_path":
        os.path.join(os.path.join(def_config()["buffer"], cres_folder)),
        "json_path":
        os.path.join(def_config()["buffer"], cres_folder,
                     simpoint_config()["json_file"].format(ptime, cltime)),
        "list_path":
        os.path.join(
            def_config()["buffer"], cres_folder,
            simpoint_config()["list_file"].format(ptime, cltime, ctime))
    }
    append_checkpoint_result(result)


def simpoint(profiling_times, cluster_times, checkpoint_times, workload):
    for ptime in range(def_config()["profiling_id"],def_config()["profiling_id"] + profiling_times):
        profiling(workload, ptime)

    #cluster
    if profiling_times != 0:
        for ptime in range(def_config()["profiling_id"], def_config()["profiling_id"] + profiling_times):
            for cltime in range(def_config()["cluster_id"],def_config()["cluster_id"] + cluster_times):
                cluster(workload, ptime, cltime)
    else:
        for cltime in range(def_config()["cluster_id"], cluster_times+def_config()["cluster_id"]):
            cluster(workload, def_config()["profiling_id"], cltime)

    #checkpoint
    #profiling -> cluster -> checkpoint
    if cluster_times != 0 and profiling_times != 0:
        for ptime in range(def_config()["profiling_id"],def_config()["profiling_id"] + profiling_times):
            for cltime in range(def_config()["cluster_id"],def_config()["cluster_id"] + cluster_times):
                for ctime in range(def_config()["checkpoint_id"],def_config()["checkpoint_id"] + checkpoint_times):
                    checkpoint(workload, ptime, cltime, ctime)

    #profiling_res -> cluster_res -> checkpoint
    elif cluster_times ==0 and profiling_times==0:
        for ctime in range(def_config()["checkpoint_id"],def_config()["checkpoint_id"] + checkpoint_times):
            checkpoint(workload,
                       def_config()["profiling_id"],
                       def_config()["cluster_id"], ctime)
    #profiling_res -> cluster -> checkpoint
    elif cluster_times != 0 and profiling_times==0:
        for cltime in range(def_config()["cluster_id"],def_config()["cluster_id"] + cluster_times):
            for ctime in range(def_config()["checkpoint_id"],def_config()["checkpoint_id"] + checkpoint_times):
                checkpoint(workload,
                           def_config()["profiling_id"], cltime, ctime)

    #profiling -> no_cluster -> checkpoint or not, donot support
    else:
        print("donot support with n profiling but 0 cluster")


def profiling_instrs(profiling_log, spec_app):
    regex = r".*total guest instructions = (.*)\x1b.*"
    with open(os.path.join(profiling_log, "{}-out.log".format(spec_app)),
              "r") as f:
        for i in f.readlines():
            if "total guest instructions" in i:
                match = re.findall(regex, i)
                match = match[0].replace(',', '')
                return match
        else:
            return 0


def cluster_weight(cluster_path, spec_app):
    points = {}
    weights = {}

    weights_path = "{}/{}/weights0".format(cluster_path, spec_app)
    simpoints_path = "{}/{}/simpoints0".format(cluster_path, spec_app)

    with open(weights_path, "r") as f:
        for line in f.readlines():
            a, b = line.split()
            weights.update({"{}".format(b): "{}".format(a)})

    with open(simpoints_path, "r") as f:
        for line in f.readlines():
            a, b = line.split()
            points.update({a: weights.get(b)})

    return points


def per_checkpoint_generate_json(profiling_log, cluster_path, app_list,
                                 target_path):
    result = {}
    for spec in app_list:
        result.update({
            spec: {
                "insts": profiling_instrs(profiling_log, spec),
                'points': cluster_weight(cluster_path, spec)
            }
        })
    with open(os.path.join(target_path), "w") as f:
        f.write(json.dumps(result))


def per_checkpoint_generate_worklist(cpt_path, target_path):
    cpt_path = cpt_path + "/"
    checkpoints = []
    for item in os.scandir(cpt_path):
        if item.is_dir():
            checkpoints.append(item.path)

    checkpoint_dirs = []
    for item in checkpoints:
        for entry in os.scandir(item):
            checkpoint_dirs.append(entry.path)

    with open(target_path, "w") as f:
        for i in checkpoint_dirs:
            path = i.replace(cpt_path, "")
            name = path.replace('/', "_", 1)
            print("{} {} 0 0 20 20".format(name, path), file=f)
