import os
import subprocess
from configs import def_config, simpoint_config
from configs import profiling_command,cluster_command,checkpoint_command
from utils import mkdir

def profiling(workload,ptime):
#    pres_folder=os.path.join(def_config()["buffer"],simpoint_config()["profiling_folder"].format(ptime))
    pres_folder=os.path.join(simpoint_config()["profiling_folder"].format(ptime))
    mkdir(pres_folder)

    profiling_out=os.path.join(simpoint_config()["profiling_logs"].format(ptime),"{}-out.log".format(workload))
    profiling_err=os.path.join(simpoint_config()["profiling_logs"].format(ptime),"{}-err.log".format(workload))

    mkdir(os.path.split(profiling_out)[0])

    print(profiling_command(workload,pres_folder),profiling_out,profiling_err)
    with open(profiling_out,"w") as out, open(profiling_err,"w") as err:
        res=subprocess.run(profiling_command(workload,pres_folder),stdout=out,stderr=err)
#        res.check_returncode()

def cluster(workload,ptime,cltime):
    pres_folder=os.path.join(def_config()["buffer"],simpoint_config()["profiling_folder"].format(ptime))
    cl_res_folder=os.path.join(def_config()["buffer"],simpoint_config()["cluster_folder"].format(ptime,cltime),workload)
    mkdir(cl_res_folder)

    cluster_out=os.path.join(simpoint_config()["cluster_logs"].format(ptime,cltime),"{}-out.log".format(workload))
    cluster_err=os.path.join(simpoint_config()["cluster_logs"].format(ptime,cltime),"{}-err.log".format(workload))

    mkdir(os.path.split(cluster_out)[0])
    print(cluster_command(workload,pres_folder,cl_res_folder),cluster_out,cluster_err)

    with open(cluster_out,"w") as out, open(cluster_err,"w") as err:
        res=subprocess.run(cluster_command(workload,pres_folder,cl_res_folder),stdout=out,stderr=err)
#        res.check_returncode()

def checkpoint(workload,ptime,cltime,ctime):
    cl_res_folder=os.path.join(def_config()["buffer"],simpoint_config()["cluster_folder"].format(ptime,cltime))
    cres_folder=os.path.join(simpoint_config()["checkpoint_folder"].format(ptime,cltime,ctime))
    mkdir(cres_folder)

    checkpoint_out=os.path.join(simpoint_config()["checkpoint_logs"].format(ptime,cltime,ctime),"{}-out.log".format(workload))
    checkpoint_err=os.path.join(simpoint_config()["checkpoint_logs"].format(ptime,cltime,ctime),"{}-err.log".format(workload))

    mkdir(os.path.split(checkpoint_out)[0])
    print(checkpoint_command(workload,cl_res_folder,cres_folder),checkpoint_out,checkpoint_err)
    with open(checkpoint_out,"w") as out, open(checkpoint_err,"w") as err:
        res=subprocess.run(checkpoint_command(workload,cl_res_folder,cres_folder),stdout=out,stderr=err)
#        res.check_returncode()

def simpoint(profiling_times,cluster_times,checkpoint_times,workload):
    for ptime in range(0,profiling_times):
        profiling(workload,ptime)

    #cluster
    if profiling_times!=0:
        for ptime in range(0,profiling_times):
            for cltime in range(0,cluster_times):
                cluster(workload,ptime,cltime)
    else:
        for cltime in range(0,cluster_times):
            cluster(workload,def_config()["profiling_id"],cltime)

    #checkpoint
    if cluster_times != 0 and profiling_times != 0:
        for ptime in range(0,profiling_times):
            for cltime in range(0,cluster_times):
                for ctime in range(0,checkpoint_times):
                    checkpoint(workload,ptime,cltime,ctime)

    elif cluster_times !=0:
       for cltime in range(0,cluster_times):
           for ctime in range(0,checkpoint_times):
               checkpoint(workload,def_config()["profiling_id"],cltime,ctime)

    else:
       for ctime in range(0,checkpoint_times):
           checkpoint(workload,def_config()["profiling_id"],def_config()["cluster_id"],ctime)
