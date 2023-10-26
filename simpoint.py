import os
import subprocess
from configs import def_config, simpoint_config
from configs import profiling_command,cluster_command,checkpoint_command
from utils import mkdir

def profiling(workload,ptime):
    pres_folder=os.path.join(def_config()["buffer"],"{}-{}".format(simpoint_config()["profiling_folder"],ptime))
    mkdir(pres_folder)

    profiling_out="{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,workload)
    profiling_err="{}-{}/{}-err.log".format(simpoint_config()["profiling_logs"],ptime,workload)

    print(profiling_command(workload,pres_folder),profiling_out,profiling_err)
#    with open(profiling_out,"w") as out, open(profiling_err,"w") as err:
#        res=subprocess.run(profiling_command(workload,pres_folder),stdout=out,stderr=err)
#        res.check_returncode()

def cluster(workload,ptime,cltime):
    pres_folder=os.path.join(def_config()["buffer"],"{}-{}".format(simpoint_config()["profiling_folder"],ptime))
    cl_res_folder=os.path.join(def_config()["buffer"],"{}-{}-{}".format(simpoint_config()["cluster_folder"],ptime,cltime))
    mkdir(cl_res_folder)

    cluster_out="{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,workload)
    cluster_err="{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,workload)

    print(cluster_command(workload,pres_folder,cl_res_folder),cluster_out,cluster_err)

#    with open(cluster_out,"w") as out, open(cluster_err,"w") as err:
#        res=subprocess.run(cluster_command(workload,pres_folder,cl_res_folder),stdout=out,stderr=err)
#        res.check_returncode()

def checkpoint(workload,ptime,cltime,ctime):
    cl_res_folder=os.path.join(def_config()["buffer"],"{}-{}-{}".format(simpoint_config()["cluster_folder"],ptime,cltime))
    cres_folder=os.path.join(def_config()["buffer"],"{}-{}-{}-{}".format(simpoint_config()["checkpoint_folder"],ptime,cltime,ctime))
    mkdir(cres_folder)

    checkpoint_out="{}-{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,ctime,workload)
    checkpoint_err="{}-{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,ctime,workload)

    print(checkpoint_command(workload,cl_res_folder,cres_folder),checkpoint_out,checkpoint_err)
#    with open(checkpoint_out,"w") as out, open(checkpoint_err,"w") as err:
#        res=subprocess.run(checkpoint_command(workload,cl_res_folder,cres_folder),stdout=out,stderr=err)
#        res.check_returncode()

def simpoint(profiling_times,cluster_times,checkpoint_times,workload):
    for ptime in range(0,profiling_times):
        profiling(workload,ptime)
#        pres_folder=os.path.join(def_config()["buffer"],"{}-{}".format(simpoint_config()["profiling_folder"],ptime))
#        mkdir(pres_folder)
#
#        profiling_out="{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,workload)
#        profiling_err="{}-{}/{}-err.log".format(simpoint_config()["profiling_logs"],ptime,workload)
#
#        print(profiling(workload,pres_folder),profiling_out,profiling_err)
#        with open(profiling_out,"w") as out, open(profiling_err,"w") as err:
#            res=subprocess.run(profiling(workload,pres_folder),stdout=out,stderr=err)
#            res.check_returncode()

    for ptime in range(0,profiling_times):
#        pres_folder=os.path.join(def_config()["buffer"],"{}-{}".format(simpoint_config()["profiling_folder"],ptime))
        for cltime in range(0,cluster_times):
            cluster(workload,ptime,cltime)
#            cl_res_folder=os.path.join(def_config()["buffer"],"{}-{}-{}".format(simpoint_config()["cluster_folder"],ptime,cltime))
#            mkdir(cl_res_folder)
#
#            cluster_out="{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,workload)
#            cluster_err="{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,workload)
#
#            print(cluster(workload,pres_folder,cl_res_folder),cluster_out,cluster_err)
#
#            with open(cluster_out,"w") as out, open(cluster_err,"w") as err:
#                res=subprocess.run(cluster(workload,pres_folder,cl_res_folder),stdout=out,stderr=err)
#                res.check_returncode()

    for ptime in range(0,profiling_times):
        for cltime in range(0,cluster_times):
#            cl_res_folder=os.path.join(def_config()["buffer"],"{}-{}-{}".format(simpoint_config()["cluster_folder"],ptime,cltime))
            for ctime in range(0,checkpoint_times):
                checkpoint(workload,ptime,cltime,ctime)
#                cres_folder=os.path.join(def_config()["buffer"],"{}-{}-{}-{}".format(simpoint_config()["cluster_folder"],ptime,cltime,ctime))
#                mkdir(cres_folder)
#
#                checkpoint_out="{}-{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,ctime,workload)
#                checkpoint_err="{}-{}-{}-{}/{}-out.log".format(simpoint_config()["profiling_logs"],ptime,cltime,ctime,workload)
#
#                print(checkpoint(workload,cl_res_folder,cres_folder),checkpoint_out,checkpoint_err)
#                with open(checkpoint_out,"w") as out, open(checkpoint_err,"w") as err:
#                    res=subprocess.run(checkpoint(workload,cl_res_folder,cres_folder),stdout=out,stderr=err)
#                    res.check_returncode()


#cluster(){
#    set -x
#    workload=$1
#    CLUSTER=$result/cluster/${workload}
#    mkdir -p $CLUSTER
#
#    random1=`head -20 /dev/urandom | cksum | cut -c 1-6`
#    random2=`head -20 /dev/urandom | cksum | cut -c 1-6`
#
#    log=$LOG_PATH/cluster_logs/
#    mkdir -p $log
#
#    $SIMPOINT \
#        -loadFVFile $PROFILING_RES/${workload}/simpoint_bbv.gz \
#        -saveSimpoints $CLUSTER/simpoints0 -saveSimpointWeights $CLUSTER/weights0 \
#        -inputVectorsGzipped -maxK 30 -numInitSeeds 2 -iters 1000 -seedkm ${random1} -seedproj ${random2} \
#        > $log/${workload}-out.txt 2> $log/${workload}-err.txt
#}


#profiling(){
#    set -x
#    workload=$1
#    log=$LOG_PATH/test-profiling_logs-o${N}
#    mkdir -p $log
#
##    $NEMU ${BBL_PATH}/vector_test \
#    $NEMU ${BBL_PATH}/${workload}-bbl-linux-spec.bin \
#        -D $result -w $workload -C $profiling_result_name       \
#        -b --simpoint-profile --cpt-interval ${interval}            \
#        -r $gcpt > $log/${workload}-out.txt 2>${log}/${workload}-err.txt
#}
#checkpoint(){
#    set -x
#    workload=$1
#
#    CLUSTER=$result/cluster
#
#    SPEC_CHECKPOINT_RES=spec-test-cpt
#    log=$LOG_PATH/checkpoint_logs/
#    mkdir -p $log
#
#    $NEMU ${BBL_PATH}/${workload}-bbl-linux-spec.bin \
#        -D $result -w ${workload} -C ${SPEC_CHECKPOINT_RES}   \
#        -b -S $CLUSTER --cpt-interval $interval \
#        -r $gcpt > $log/${workload}-out.txt 2>$log/${workload}-err.txt 
#}
