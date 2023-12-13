<a name="OH3kA"></a>
## 环境准备
- 请预先准备好riscv64工具链，可能用到的prefix有`riscv64-linux-gnu-` `riscv64-unknown-linux-gnu-` `riscv64-unknown-elf-`
- 从香山项目中克隆下来 riscv-pk， riscv-linux， riscv-rootfs，NEMU分别是启动加载程序 Bootloader， Linux kernel ，根文件系统 rootfs和NEMU。请将四个仓库放到同一目录下
   - https://github.com/OpenXiangShan/riscv-pk noop 分支
   - https://github.com/OpenXiangShan/riscv-linux nanshan 分支
   - https://github.com/OpenXiangShan/riscv-rootfs checkpoint 分支
   - [https://github.com/OpenXiangShan/NEMU](https://github.com/OpenXiangShan/NEMU/tree/master) master 分支
- 设置环境变量
   - NEMU_HOME：NEMU 的路径
   - NOOP_HOME：XiangShan 的路径
   - RISCV_ROOTFS_HOME：riscv-rootfs 的路径
   - RISCV：riscv-gnu-toolchain 的安装路径（包含bin， include， lib等的顶层目录路径）
- 准备工作
   - 配置 Linux Kernel
      - 到 riscv-linux 目录
      - 使用 fpga_defconfig 配置，命令为make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- fpga_defconfig
      - 根据自己的需求酌情通过 menuconfig 做修改，命令为make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- menuconfig ，其中一个较为**必要的修改**是将 initramfs 的 source 从${RISCV_ROOTFS_HOME}/rootfsimg/initramfs.txt 改为  ${RISCV_ROOTFS_HOME}/rootfsimg/initramfs-spec.txt
   - 重新配置 BBL
      - 到 riscv-pk 目录
      - 修改 dts 中地址空间大小，支持占用内存更大的程序运行
      ```

      L11: memory@100000000 {
          device_type = "memory";
          -reg = <0x0 0x80000000 0x0 0x2000000>;
          +reg = <0x0 0x80000000 0x0 0x80000000>;
      };
      ```

      - 应用[https://github.com/riscv-software-src/riscv-pk/commit/4ae5a8876fc2c31776b1777405ab14f764cc0f36](https://github.com/riscv-software-src/riscv-pk/commit/4ae5a8876fc2c31776b1777405ab14f764cc0f36)这个commit
      - NEMU在生成checkpoint时，需要添加一段恢复程序。因此在生成workload时需要避开这段空间。在riscv-pk/bbl/bbl.lds中修改 . 地址为MEM_START + 0xa0000 即 . = MEM_START + 0xa0000
   - 编译NEMU
      - 使用 git submodule update --init下载同步
      - 在NEMU/resource/simpoint/simpoint_repo目录下执行make得到可执行文件NEMU/resource/simpoint/simpoint_repo/bin/simpoint
      - 在NEMU/目录下执行make riscv64-xs_defconfig然后make menuconfig自行调整所需的选项，然后执行make
      - 在NEMU/resource/gcpt_restore目录下执行make命令编译得到gcpt.bin
<a name="yiJVh"></a>
## 一键checkpoint

- 克隆这个仓库[https://github.com/xyyy1420/auto_checkpoint](https://github.com/xyyy1420/auto_checkpoint) 到任意目录
- 参数说明
```
usage: generate_checkpoint.py [-h] [--elfs ELFS] [--archive-folder ARCHIVE_FOLDER] [--elf-suffix ELF_SUFFIX] [--spec-app-list SPEC_APP_LIST] [--print-spec-app-list] [--message MESSAGE] [--spec-bbl-checkpoint-mode] [--profiling-times PROFILING_TIMES]
                              [--cluster-times CLUSTER_TIMES] [--checkpoint-times CHECKPOINT_TIMES] [--profiling-id PROFILING_ID] [--cluster-id CLUSTER_ID] [--checkpoint-id CHECKPOINT_ID] [--archive-id ARCHIVE_ID] [--max-threads MAX_THREADS] [--build-bbl-only]

Auto profiling and checkpointing

optional arguments:
  -h, --help            show this help message and exit
  --elfs ELFS           指定编译好的spec elf文件所在目录，其中的文件名需要至少包含spec程序的basename，可以随意加前后缀，但是同一个basename的spec程序只能放一个，并且文件全名中不应该同时包含两个spec的basename
  --archive-folder ARCHIVE_FOLDER
                        所有的bin、elf、profiling、cluster、checkpoint、log结果都会保存到archive目录下的某个子目录中 (默认使用archive作为目录名)
  --elf-suffix ELF_SUFFIX
                        编译到bin文件中的elf可以自定义加后缀
  --spec-app-list SPEC_APP_LIST
                        准备checkpoint的spec程序的list，可以用--print-spec-app-list选项输出所有的spec程序名字
  --print-spec-app-list
                        输出所有的spec程序名字
  --message MESSAGE     为archive中每个子目录记录一条信息，用于提示checkpoint的配置等，支持使用下述选项指定已有的archive id
  --spec-bbl-checkpoint-mode
                        使用该选项会在bbl中内置before_workload和trap
  --times TIMES
                        profiling，cluster，checkpoint的次数指定，格式是 profiling_times,cluster_times,checkpoint_times 意思是运行profiling_times次profiling，每次profiling运行cluster_times次cluster，每次cluster运行checkpoint_times次checkpoint
  --start-id START_ID
                        指定本次运行从id开始计数，如果设置了profiling，cluster，checkpoint中某个的times为0，则表示使用id指示的profiling，cluster，checkpoint中的结果
  --archive-id ARCHIVE_ID
                        archive id
  --max-threads MAX_THREADS
                        自动化checkpoint过程中最大可使用的线程数，目前还没支持多次cluster和多次checkpoint的并行，因此线程数最大设置为spec程序数就足够了，并且并没有用这个参数控制构建bin文件时的线程数
  --build-bbl-only      只生成bin文件不进行profiling以及后续操作
```

- 调整config.py文件，
   - 将riscv-rootfs，pk，nemu_home改为上文中环境准备过程中自己的riscv-rootfs/rootfsimg的路径，riscv-pk路径，nemu路径，其他内容不需要修改
- 一键checkpoint
```
python3 generate_checkpoint.py --elfs ./gcc_elfs --spec-app-list ./gcc.lst --message "First gcc checkpoint" --spec-bbl-checkpoint-mode --max-threads 100
```

   - 其他选项参考上述说明
   - **注意**：
      - 运行后请在几分钟内查看log确认workload正常运行，在某些情况下会存在workload已经结束运行但是运行workload的进程并没有结束的情况（没有使用before_workload、trap或者运行过程中出错）
      - 如果输出提示build xxxxxxx此时请不要再次运行这个脚本，等待开始输出profiling命令后可以开始运行另外一个进程，原因是构建workload的过程无法同时进行。
      - 无论是否会运行出错，每个阶段的log都会保存在archive/archive_id/logs中
      - 运行脚本后会在运行目录生成一个auto_checkpoint_env.sh文件，可以方便的在不同服务器间配置相同的环境变量
- 最终结果示例
   - 运行过程中会输出一些log，按顺序依次是正在构建bin文件的提示，执行profiling、cluster、checkpoint的提示，最后是最终获得的结果（如下图）（新版不会输出这些path，而是提供一个result文件的path，其中包含了需要的路径）
   - ![image.png](https://cdn.nlark.com/yuque/0/2023/png/35441298/1698738798309-d468ccb0-a8a4-43a7-9a38-04255e7f1b8d.png#averageHue=%23322e29&clientId=u5a84fd58-4228-4&from=paste&height=53&id=uc8172663&originHeight=80&originWidth=990&originalType=binary&ratio=1.5&rotation=0&showTitle=false&size=16512&status=done&style=none&taskId=u6d72a0cf-96ff-4ad8-a177-452d7fabd62&title=&width=660)
   - 可以在archive目录下的archive_info文件中找到所有的archive id以及对应的message
   - ![image.png](https://cdn.nlark.com/yuque/0/2023/png/35441298/1698740669236-0a10fa9e-d5c5-4226-8fb5-05f86db6f7d6.png#averageHue=%232a2724&clientId=u5a84fd58-4228-4&from=paste&height=35&id=u8ed3ddab&originHeight=53&originWidth=710&originalType=binary&ratio=1.5&rotation=0&showTitle=false&size=6659&status=done&style=none&taskId=uec660434-a6cc-4782-a7db-6440afb0c2b&title=&width=473.3333333333333)
- **TODO**：
   - ⚡通过设置一个flag文件阻止多个进程在构建过程中同时运行
   - 运行过程出错之后再次运行应该接着未完成的任务继续❌
   - 支持删除出错流程中生成的文件✔️
   - 支持通过命令行读入各种配置文件（按照一定格式）
   - 支持通过命令行读入workload list，或者某些可选的list标志，而不是一定需要一个lst文件✔️
   - ⚡支持将结果转为绝对路径输出到某处 ✔️
   - 删除生成的simpoint_bbv文件夹（不是脚本生成的，可能是nemu或者cluster，还没详细看）✔️
   - 生成path文件，以适配xy的脚本
   - ⚡支持在cluster阶段和checkpoint阶段的并行化（主要是解决线程数量的合理分配）
   - ⚡增加版本号以区分新增的功能点❌
   - ⚡运行出错后下一次运行会继承运行出错时的archive-id，需要看看是啥原因✔️
   - ⚡彻底修正SPEC程序名称匹配到gcc的问题❌
   - ⚡使用随机单词替换md5✔️

⚡表示高优先级，✔️表示已完成，❌表示不需要继续修复
