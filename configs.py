import multiprocessing
from os.path import realpath
import os
import random

manager = multiprocessing.Manager()
checkpoint_res = manager.list()
checkpoint_lock = manager.Lock()


def append_checkpoint_result(res):
    checkpoint_lock.acquire()
    if res not in checkpoint_res:
        checkpoint_res.append(res)
    checkpoint_lock.release()


def get_checkpoint_results():
    checkpoint_lock.acquire()
    res = checkpoint_res
    checkpoint_lock.release()
    return res


default_config = {
    "logs": "logs",
    "buffer": "test_buffer",
    "archive_folder": "archive",
    "elf_suffix": "_base.riscv64-linux-gnu-gcc12.2.0",
    "bin_suffix": "-bbl-linux-spec.bin",
    "cpu2006_run_dir":
    "/path/to/cpu2006_run_dir",
    "riscv-rootfs": "/path/to/rootfsimg",
    "pk": "/path/to/riscv-pk",
    "nemu_home": "/path/to/NEMU",
    "profiling_times": 1,
    "cluster_times": 1,
    "checkpoint_times": 1,
    "profiling_id": 0,
    "cluster_id": 0,
    "checkpoint_id": 0
}


def def_config():
    return default_config


def prepare_config():
    return {
        "prepare_log":
        os.path.join(def_config()["buffer"],
                     def_config()["logs"], "prepare"),
        "elf_folder":
        os.path.join(def_config()["buffer"], "elf"),
    }


def build_config():
    return {
        "build_log":
        os.path.join(def_config()["buffer"],
                     def_config()["logs"], "build"),
        "bin_folder":
        os.path.join(def_config()["buffer"], "bin")
    }


default_simpoint_config = {
    "profiling_format": "profiling-{}",
    "cluster_format": "cluster-{}-{}",
    "checkpoint_format": "checkpoint-{}-{}-{}",
    "json_format": "cluster-{}-{}.json",
    "list_format": "checkpoint-{}-{}-{}.lst",
}


#default_simpoint_config=
def simpoint_config():
    return {
        "nemu":
        os.path.join(def_config()["nemu_home"], "build",
                     "riscv64-nemu-interpreter"),
        "gcpt_restore":
        os.path.join(def_config()["nemu_home"], "resource", "gcpt_restore",
                     "build", "gcpt.bin"),
        "simpoint":
        os.path.join(def_config()["nemu_home"], "resource", "simpoint",
                     "simpoint_repo", "bin", "simpoint"),
        "bbl_folder":
        os.path.join(build_config()["bin_folder"]),
        "profiling_folder":
        default_simpoint_config["profiling_format"],
        "cluster_folder":
        default_simpoint_config["cluster_format"],
        "checkpoint_folder":
        default_simpoint_config["checkpoint_format"],
        "json_file":
        default_simpoint_config["json_format"],
        "list_file":
        default_simpoint_config["list_format"],
        "profiling_logs":
        os.path.join(def_config()["buffer"],
                     def_config()["logs"],
                     default_simpoint_config["profiling_format"]),
        "cluster_logs":
        os.path.join(def_config()["buffer"],
                     def_config()["logs"],
                     default_simpoint_config["cluster_format"]),
        "checkpoint_logs":
        os.path.join(def_config()["buffer"],
                     def_config()["logs"],
                     default_simpoint_config["checkpoint_format"]),
        "interval":
        "20000000",
    }


def profiling_command(workload, profiling_folder):
    command = [
        simpoint_config()["nemu"],
        "{}/{}{}".format(simpoint_config()["bbl_folder"], workload,
                         def_config()["bin_suffix"]), "-D",
        def_config()["buffer"], "-w", workload, "-C", profiling_folder, "-b",
        "--simpoint-profile", "--cpt-interval",
        simpoint_config()["interval"], "-r",
        simpoint_config()["gcpt_restore"]
    ]
    return command


def cluster_command(workload, profiling_folder, cluster_folder):
    seedkm = random.randint(100000, 999999)
    seedproj = random.randint(100000, 999999)
    command = [
        simpoint_config()["simpoint"], "-loadFVFile",
        os.path.join(profiling_folder, workload,
                     "simpoint_bbv.gz"), "-saveSimpoints",
        os.path.join(cluster_folder, "simpoints0"), "-saveSimpointWeights",
        os.path.join(cluster_folder, "weights0"), "-inputVectorsGzipped",
        "-maxK", "30", "-numInitSeeds", "2", "-iters", "1000", "-seedkm",
        f"{seedkm}", "-seedproj", f"{seedproj}"
    ]
    return command


def checkpoint_command(workload, cluster_folder, checkpoint_folder):
    command = [
        simpoint_config()["nemu"],
        "{}/{}{}".format(simpoint_config()["bbl_folder"], workload,
                         def_config()["bin_suffix"]), "-D",
        def_config()["buffer"], "-w", workload, "-C", checkpoint_folder, "-b",
        "-S", cluster_folder, "--cpt-interval",
        simpoint_config()["interval"], "-r",
        simpoint_config()["gcpt_restore"]
    ]
    return command


default_initramfs_file = [
    "dir /bin 755 0 0", "dir /etc 755 0 0", "dir /dev 755 0 0",
    "dir /lib 755 0 0", "dir /proc 755 0 0", "dir /sbin 755 0 0",
    "dir /sys 755 0 0", "dir /tmp 755 0 0", "dir /usr 755 0 0",
    "dir /mnt 755 0 0", "dir /usr/bin 755 0 0", "dir /usr/lib 755 0 0",
    "dir /usr/sbin 755 0 0", "dir /var 755 0 0", "dir /var/tmp 755 0 0",
    "dir /root 755 0 0", "dir /var/log 755 0 0", "",
    "nod /dev/console 644 0 0 c 5 1", "nod /dev/null 644 0 0 c 1 3", "",
    "# libraries",
    "file /lib/ld-linux-riscv64-lp64d.so.1 ${RISCV}/sysroot/lib/ld-linux-riscv64-lp64d.so.1 755 0 0",
    "file /lib/libc.so.6 ${RISCV}/sysroot/lib/libc.so.6 755 0 0",
    "file /lib/libresolv.so.2 ${RISCV}/sysroot/lib/libresolv.so.2 755 0 0",
    "file /lib/libm.so.6 ${RISCV}/sysroot/lib/libm.so.6 755 0 0",
    "file /lib/libdl.so.2 ${RISCV}/sysroot/lib/libdl.so.2 755 0 0",
    "file /lib/libpthread.so.0 ${RISCV}/sysroot/lib/libpthread.so.0 755 0 0",
    "", "# busybox",
    "file /bin/busybox ${RISCV_ROOTFS_HOME}/rootfsimg/build/busybox 755 0 0",
    "file /etc/inittab ${RISCV_ROOTFS_HOME}/rootfsimg/inittab-spec 755 0 0",
    "slink /init /bin/busybox 755 0 0", "", "# SPEC common",
    "dir /spec_common 755 0 0",
    "file /spec_common/before_workload ${RISCV_ROOTFS_HOME}/rootfsimg/build/before_workload 755 0 0",
    "file /spec_common/trap ${RISCV_ROOTFS_HOME}/rootfsimg/build/trap 755 0 0", "", "# SPEC",
    "dir /spec 755 0 0",
    "file /spec/run.sh ${RISCV_ROOTFS_HOME}/rootfsimg/run.sh 755 0 0"
]

def get_spec_elf_list():
    return [
        "astar", "bwaves", "bzip2", "cactusADM", "calculix", "dealII",
        "gamess", "GemsFDTD", "gobmk", "gromacs", "h264ref", "hmmer",
        "lbm", "leslie3d", "libquantum", "mcf", "milc", "namd", "omnetpp",
        "perlbench", "povray", "sjeng", "soplex", "specrand", "sphinx3",
        "tonto", "wrf", "xalancbmk", "zeusmp", "gcc"
    ]


def get_default_spec_list():
    return [
        "astar_biglakes",
        "astar_rivers",
        "bwaves",
        "bzip2_chicken",
        "bzip2_combined",
        "bzip2_html",
        "bzip2_liberty",
        "bzip2_program",
        "bzip2_source",
        "cactusADM",
        "calculix",
        "dealII",
        "gamess_cytosine",
        "gamess_gradient",
        "gamess_triazolium",
        "gcc_166",
        "gcc_200",
        "gcc_cpdecl",
        "gcc_expr2",
        "gcc_expr",
        "gcc_g23",
        "gcc_s04",
        "gcc_scilab",
        "gcc_typeck",
        "GemsFDTD",
        "gobmk_13x13",
        "gobmk_nngs",
        "gobmk_score2",
        "gobmk_trevorc",
        "gobmk_trevord",
        "gromacs",
        "h264ref_foreman.baseline",
        "h264ref_foreman.main",
        "h264ref_sss",
        "hmmer_nph3",
        "hmmer_retro",
        "lbm",
        "leslie3d",
        "libquantum",
        "mcf",
        "milc",
        "namd",
        "omnetpp",
        "perlbench_checkspam",
        "perlbench_diffmail",
        "perlbench_splitmail",
        "povray",
        "sjeng",
        "soplex_pds-50",
        "soplex_ref",
        "sphinx3",
        "tonto",
        "wrf",
        "xalancbmk",
        "zeusmp",
    ]


def get_spec_info(cpu2006_run_dir, buffer, elf_suffix):
    cpu2006_run_dir = realpath(cpu2006_run_dir)
    buffer = realpath(buffer)
    return {
        "astar_biglakes": ([
            f"{buffer}/astar" + elf_suffix,
            f"{cpu2006_run_dir}/astar/BigLakes2048.bin",
            f"{cpu2006_run_dir}/astar/BigLakes2048.cfg"
        ], ["BigLakes2048.cfg"], ["int", "ref"]),
        "astar_rivers": ([
            f"{buffer}/astar" + elf_suffix,
            f"{cpu2006_run_dir}/astar/rivers.bin",
            f"{cpu2006_run_dir}/astar/rivers.cfg"
        ], ["rivers.cfg"], ["int", "ref"]),
        "bwaves": ([
            f"{buffer}/bwaves" + elf_suffix,
            f"{cpu2006_run_dir}/bwaves/bwaves.in"
        ], [], ["fp", "ref"]),
        "bzip2_chicken": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/chicken.jpg"
        ], ["chicken.jpg", "30"], ["int", "ref"]),
        "bzip2_combined": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/input.combined"
        ], ["input.combined", "200"], ["int", "ref"]),
        "bzip2_html": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/text.html"
        ], ["text.html", "280"], ["int", "ref"]),
        "bzip2_liberty": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/liberty.jpg"
        ], ["liberty.jpg", "30"], ["int", "ref"]),
        "bzip2_program": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/input.program"
        ], ["input.program", "280"], ["int", "ref"]),
        "bzip2_source": ([
            f"{buffer}/bzip2" + elf_suffix,
            f"{cpu2006_run_dir}/bzip2/input.source"
        ], ["input.source", "280"], ["int", "ref"]),
        "cactusADM": ([
            f"{buffer}/cactusADM" + elf_suffix,
            f"{cpu2006_run_dir}/cactusADM/benchADM.par"
        ], ["benchADM.par"], ["fp", "ref"]),
        "calculix": ([
            f"{buffer}/calculix" + elf_suffix,
            f"{cpu2006_run_dir}/calculix/hyperviscoplastic.dat",
            f"{cpu2006_run_dir}/calculix/hyperviscoplastic.frd",
            f"{cpu2006_run_dir}/calculix/hyperviscoplastic.inp",
            f"{cpu2006_run_dir}/calculix/hyperviscoplastic.sta"
        ], ["-i", "hyperviscoplastic"], ["fp", "ref"]),
        "dealII": ([
            f"{buffer}/dealII" + elf_suffix,
            f"{cpu2006_run_dir}/dealII/DummyData"
        ], ["23"], ["fp", "ref"]),
        "gamess_cytosine": ([
            f"{buffer}/gamess" + elf_suffix,
            f"{cpu2006_run_dir}/gamess/cytosine.2.config",
            f"{cpu2006_run_dir}/gamess/cytosine.2.inp"
        ], ["<", "cytosine.2.config"], ["fp", "ref"]),
        "gamess_gradient": ([
            f"{buffer}/gamess" + elf_suffix,
            f"{cpu2006_run_dir}/gamess/h2ocu2+.gradient.config",
            f"{cpu2006_run_dir}/gamess/h2ocu2+.gradient.inp"
        ], ["<", "h2ocu2+.gradient.config"], ["fp", "ref"]),
        "gamess_triazolium": ([
            f"{buffer}/gamess" + elf_suffix,
            f"{cpu2006_run_dir}/gamess/triazolium.config",
            f"{cpu2006_run_dir}/gamess/triazolium.inp"
        ], ["<", "triazolium.config"], ["fp", "ref"]),
        "gcc_166":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/166.i"], ["166.i", "-o",
                                            "166.s"], ["int", "ref"]),
        "gcc_200":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/200.i"], ["200.i", "-o",
                                            "200.s"], ["int", "ref"]),
        "gcc_cpdecl":
        ([f"{buffer}/gcc" + elf_suffix, f"{cpu2006_run_dir}/gcc/cp-decl.i"],
         ["cp-decl.i", "-o", "cp-decl.s"], ["int", "ref"]),
        "gcc_expr2":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/expr2.i"], ["expr2.i", "-o",
                                              "expr2.s"], ["int", "ref"]),
        "gcc_expr":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/expr.i"], ["expr.i", "-o",
                                             "expr.s"], ["int", "ref"]),
        "gcc_g23":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/g23.i"], ["g23.i", "-o",
                                            "g23.s"], ["int", "ref"]),
        "gcc_s04":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/s04.i"], ["s04.i", "-o",
                                            "s04.s"], ["int", "ref"]),
        "gcc_scilab":
        ([f"{buffer}/gcc" + elf_suffix,
          f"{cpu2006_run_dir}/gcc/scilab.i"], ["scilab.i", "-o",
                                               "scilab.s"], ["int", "ref"]),
        "gcc_typeck": ([
            f"{buffer}/gcc" + elf_suffix, f"{cpu2006_run_dir}/gcc/c-typeck.i"
        ], ["c-typeck.i", "-o", "c-typeck.s"], ["int", "ref"]),
        "GemsFDTD": ([
            f"{buffer}/GemsFDTD" + elf_suffix,
            f"{cpu2006_run_dir}/GemsFDTD/ref.in",
            f"{cpu2006_run_dir}/GemsFDTD/sphere.pec",
            f"{cpu2006_run_dir}/GemsFDTD/yee.dat"
        ], [], ["fp", "ref"]),
        "gobmk_13x13": ([
            f"{buffer}/gobmk" + elf_suffix,
            f"{cpu2006_run_dir}/gobmk/13x13.tst",
            f"dir games {cpu2006_run_dir}/gobmk/games",
            f"dir golois {cpu2006_run_dir}/gobmk/golois"
        ], ["--quiet", "--mode", "gtp", "<", "13x13.tst"], ["int", "ref"]),
        "gobmk_nngs": ([
            f"{buffer}/gobmk" + elf_suffix,
            f"{cpu2006_run_dir}/gobmk/nngs.tst",
            f"dir games {cpu2006_run_dir}/gobmk/games",
            f"dir golois {cpu2006_run_dir}/gobmk/golois"
        ], ["--quiet", "--mode", "gtp", "<", "nngs.tst"], ["int", "ref"]),
        "gobmk_score2": ([
            f"{buffer}/gobmk" + elf_suffix,
            f"{cpu2006_run_dir}/gobmk/score2.tst",
            f"dir games {cpu2006_run_dir}/gobmk/games",
            f"dir golois {cpu2006_run_dir}/gobmk/golois"
        ], ["--quiet", "--mode", "gtp", "<", "score2.tst"], ["int", "ref"]),
        "gobmk_trevorc": ([
            f"{buffer}/gobmk" + elf_suffix,
            f"{cpu2006_run_dir}/gobmk/trevorc.tst",
            f"dir games {cpu2006_run_dir}/gobmk/games",
            f"dir golois {cpu2006_run_dir}/gobmk/golois"
        ], ["--quiet", "--mode", "gtp", "<", "trevorc.tst"], ["int", "ref"]),
        "gobmk_trevord": ([
            f"{buffer}/gobmk" + elf_suffix,
            f"{cpu2006_run_dir}/gobmk/trevord.tst",
            f"dir games {cpu2006_run_dir}/gobmk/games",
            f"dir golois {cpu2006_run_dir}/gobmk/golois"
        ], ["--quiet", "--mode", "gtp", "<", "trevord.tst"], ["int", "ref"]),
        "gromacs": ([
            f"{buffer}/gromacs" + elf_suffix,
            f"{cpu2006_run_dir}/gromacs/gromacs.tpr"
        ], ["-silent", "-deffnm", "gromacs.tpr", "-nice", "0"], ["fp", "ref"]),
        "h264ref_foreman.baseline": ([
            f"{buffer}/h264ref" + elf_suffix,
            f"{cpu2006_run_dir}/h264ref/foreman_ref_encoder_baseline.cfg",
            f"{cpu2006_run_dir}/h264ref/foreman_qcif.yuv"
        ], ["-d", "foreman_ref_encoder_baseline.cfg"], ["int", "ref"]),
        "h264ref_foreman.main": ([
            f"{buffer}/h264ref" + elf_suffix,
            f"{cpu2006_run_dir}/h264ref/foreman_ref_encoder_main.cfg",
            f"{cpu2006_run_dir}/h264ref/foreman_qcif.yuv"
        ], ["-d", "foreman_ref_encoder_main.cfg"], ["int", "ref"]),
        "h264ref_sss": ([
            f"{buffer}/h264ref" + elf_suffix,
            f"{cpu2006_run_dir}/h264ref/sss_encoder_main.cfg",
            f"{cpu2006_run_dir}/h264ref/sss.yuv"
        ], ["-d", "sss_encoder_main.cfg"], ["int", "ref"]),
        "hmmer_nph3": ([
            f"{buffer}/hmmer" + elf_suffix,
            f"{cpu2006_run_dir}/hmmer/nph3.hmm",
            f"{cpu2006_run_dir}/hmmer/swiss41"
        ], ["nph3.hmm", "swiss41"], ["int", "ref"]),
        "hmmer_retro": ([
            f"{buffer}/hmmer" + elf_suffix,
            f"{cpu2006_run_dir}/hmmer/retro.hmm"
        ], [
            "--fixed", "0", "--mean", "500", "--num", "500000", "--sd", "350",
            "--seed", "0", "retro.hmm"
        ], ["int", "ref"]),
        "lbm": ([
            f"{buffer}/lbm" + elf_suffix,
            f"{cpu2006_run_dir}/lbm/100_100_130_ldc.of",
            f"{cpu2006_run_dir}/lbm/lbm.in"
        ], ["3000", "reference.dat", "0", "0",
            "100_100_130_ldc.of"], ["fp", "ref"]),
        "leslie3d": ([
            f"{buffer}/leslie3d" + elf_suffix,
            f"{cpu2006_run_dir}/leslie3d/leslie3d.in"
        ], ["<", "leslie3d.in"], ["fp", "ref"]),
        "libquantum": ([f"{buffer}/libquantum" + elf_suffix], ["1397", "8"],
                       ["int", "ref"]),
        "mcf":
        ([f"{buffer}/mcf" + elf_suffix,
          f"{cpu2006_run_dir}/mcf/inp.in"], ["inp.in"], ["int", "ref"]),
        "milc":
        ([f"{buffer}/milc" + elf_suffix,
          f"{cpu2006_run_dir}/milc/su3imp.in"], ["<",
                                                 "su3imp.in"], ["fp", "ref"]),
        "namd":
        ([f"{buffer}/namd" + elf_suffix,
          f"{cpu2006_run_dir}/namd/namd.input"], [
              "--input", "namd.input", "--iterations", "38", "--output",
              "namd.out"
          ], ["fp", "ref"]),
        "omnetpp": ([
            f"{buffer}/omnetpp" + elf_suffix,
            f"{cpu2006_run_dir}/omnetpp/omnetpp.ini"
        ], ["omnetpp.ini"], ["int", "ref"]),
        "perlbench_checkspam": ([
            f"{buffer}/perlbench" + elf_suffix,
            f"{cpu2006_run_dir}/perlbench/cpu2006_mhonarc.rc",
            f"{cpu2006_run_dir}/perlbench/checkspam.pl",
            f"{cpu2006_run_dir}/perlbench/checkspam.in",
            f"dir lib {cpu2006_run_dir}/perlbench/lib",
            f"dir rules {cpu2006_run_dir}/perlbench/rules"
        ], [
            "-I./lib", "checkspam.pl", "2500", "5", "25", "11", "150", "1",
            "1", "1", "1"
        ], ["int", "ref"]),
        "perlbench_diffmail": ([
            f"{buffer}/perlbench" + elf_suffix,
            f"{cpu2006_run_dir}/perlbench/cpu2006_mhonarc.rc",
            f"{cpu2006_run_dir}/perlbench/diffmail.pl",
            f"{cpu2006_run_dir}/perlbench/diffmail.in",
            f"dir lib {cpu2006_run_dir}/perlbench/lib",
            f"dir rules {cpu2006_run_dir}/perlbench/rules"
        ], ["-I./lib", "diffmail.pl", "4", "800", "10", "17", "19",
            "300"], ["int", "ref"]),
        "perlbench_splitmail": ([
            f"{buffer}/perlbench" + elf_suffix,
            f"{cpu2006_run_dir}/perlbench/cpu2006_mhonarc.rc",
            f"{cpu2006_run_dir}/perlbench/splitmail.pl",
            f"{cpu2006_run_dir}/perlbench/splitmail.in",
            f"dir lib {cpu2006_run_dir}/perlbench/lib",
            f"dir rules {cpu2006_run_dir}/perlbench/rules"
        ], ["-I./lib", "splitmail.pl", "1600", "12", "26", "16",
            "4500"], ["int", "ref"]),
        "povray": ([
            f"{buffer}/povray" + elf_suffix, f"dir . {cpu2006_run_dir}/povray"
        ], ["SPEC-benchmark-ref.ini"], ["fp", "ref"]),
        "sjeng": ([
            f"{buffer}/sjeng" + elf_suffix, f"{cpu2006_run_dir}/sjeng/ref.txt"
        ], ["ref.txt"], ["int", "ref"]),
        "soplex_pds-50": ([
            f"{buffer}/soplex" + elf_suffix,
            f"{cpu2006_run_dir}/soplex/pds-50.mps"
        ], ["-s1", "-e", "-m45000", "pds-50.mps"], ["fp", "ref"]),
        "soplex_ref": ([
            f"{buffer}/soplex" + elf_suffix,
            f"{cpu2006_run_dir}/soplex/ref.mps"
        ], ["-m3500", "ref.mps"], ["fp", "ref"]),
        "sphinx3": ([
            f"{buffer}/sphinx3" + elf_suffix,
            f"dir . {cpu2006_run_dir}/sphinx3"
        ], ["ctlfile", ".", "args.an4"], ["fp", "ref"]),
        "tonto": ([
            f"{buffer}/tonto" + elf_suffix, f"{cpu2006_run_dir}/tonto/stdin"
        ], [], ["fp", "ref"]),
        "wrf": ([f"{buffer}/wrf" + elf_suffix,
                 f"dir . {cpu2006_run_dir}/wrf"], [], ["fp", "ref"]),
        "xalancbmk": ([
            f"{buffer}/xalancbmk" + elf_suffix,
            f"dir . {cpu2006_run_dir}/xalancbmk"
        ], ["-v", "t5.xml", "xalanc.xsl"], ["int", "ref"]),
        "zeusmp": ([
            f"{buffer}/zeusmp" + elf_suffix,
            f"{cpu2006_run_dir}/zeusmp/zmp_inp"
        ], [], ["fp", "ref"]),
        # WARNING: this is SPEC test
        "gamess_exam29": ([
            f"{buffer}/gamess" + elf_suffix,
            f"{cpu2006_run_dir}/gamess/exam29.config",
            f"{cpu2006_run_dir}/gamess/exam29.inp"
        ], ["<", "exam29.config"], ["fp", "test"]),
    }
