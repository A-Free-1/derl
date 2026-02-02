"""Script to evovle morphology."""

import argparse
import os
import random
import signal
import subprocess
import sys
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import networkx as nx

from derl.config import cfg
from derl.config import dump_cfg
from derl.envs.morphology import SymmetricUnimal
from derl.utils import evo as eu
from derl.utils import file as fu
from derl.utils import sample as su
from derl.utils import similarity as simu


"""The script assumes the following folder structure.

cfg.OUT_DIR
    - models
    - metadata
    - xml
    - unimal_init
    - rewards

The evolution code has the following structure:
-- init_population
-- evolve_population
    1. select unimals to evolve
    2. evolve unimal. Save the mujoco xml (in xml) and save data required to
       instantiate the unimal class (in unimal_init). See SymmetricUnimal
    3. train unimal. Save the weights (in models). Finally save metadata like
       rews etc used in step 1.

Files inside metadata correspond to actual unimals in the population. Since we
use spot instances only if metadata file is present we can be sure all other
corresponding files will be present.

Distributed Training Setup: evolution.py is launched in parallel on multiple
cpu nodes. Node id can be identified by cfg.NODE_ID leveraging aws apis.
Each evolution script launches cfg.EVO.NUM_PROCESSES parallel subprocs.
For supporting SubprocEnv we need to use subprocess. Refer:
https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
"""

# 计算PPO训练的最大迭代次数
def calculate_max_iters():
    # Iter here refers to 1 cycle of experience collection and policy update.
    cfg.PPO.MAX_ITERS = (
        int(cfg.PPO.MAX_STATE_ACTION_PAIRS) # 总状态-动作对数量
        // cfg.PPO.TIMESTEPS
        // cfg.PPO.NUM_ENVS
    )
# 最大迭代次数 = 总状态动作对 ÷ (时间步 × 环境数)

# 创建输出目录结构
def setup_output_dir():
    os.makedirs(cfg.OUT_DIR, exist_ok=True)
    # Make subfolders
    subfolders = [
        "models",   # 保存训练好的神经网络权重
        "metadata", # 保存与每个unimal相关的元数据文件
        "xml",
        "unimal_init",
        "rewards",
        "videos",
        "error_metadata",
        "images",
    ]
    for folder in subfolders:
        os.makedirs(os.path.join(cfg.OUT_DIR, folder), exist_ok=True)


def parse_args():
    """Parses the arguments."""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Train a RL agent")
    parser.add_argument(
        "--cfg", dest="cfg_file", help="Config file", required=True, type=str
    )
    parser.add_argument(
        "opts",
        help="See morphology/config.py for all options",
        default=None,
        nargs=argparse.REMAINDER,
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()
# python evolution.py --cfg configs/default.yaml PPO.LR 0.0003 EVO.POP_SIZE 100

def wait_till_init():
    # 非主节点等待主节点完成初始种群创建
    init_setup_done_path = os.path.join(cfg.OUT_DIR, "init_setup_done")
    max_wait = 3600  # one hour
    time_waited = 0
    # 等待初始种群创建完成的标志文件出现
    # 这是无中心协调器的分布式同步方法
    while not os.path.exists(init_setup_done_path):
        time.sleep(60)
        time_waited += 60
        if time_waited >= max_wait:
            print("Initial xmls not made. Exiting!")
            sys.exit(1)


def limb_count_pop_init(idx, unimal_id):
    # Build unimals which initialize the population based on number of limbs.
    # 基于肢体数量初始化种群
    # 创建对称结构的unimal
    # unimal_id格式：节点ID-索引-时间戳
    # 随机采样肢体数量
    # 首次生长一个肢体
    # 然后不断变异直到达到目标肢体数量
    unimal = SymmetricUnimal(unimal_id)
    num_limbs = su.sample_from_range(cfg.LIMB.NUM_LIMBS_RANGE)
    unimal.mutate(op="grow_limb")
    # 随机变异直到达到目标肢体数量
    while unimal.num_limbs < num_limbs:
        unimal.mutate()
    # 保存unimal的xml和初始化数据
    unimal.save()
    return unimal_id


def create_init_unimals():
    # 主节点创建初始种群
    init_setup_done_path = os.path.join(cfg.OUT_DIR, "init_setup_done")
    # 如果初始种群已经创建则直接返回
    # 检查是否已经创建了初始种群
    if os.path.isfile(init_setup_done_path):
        print("Init xmls have already been.")
        return
    # 获取初始种群大小（目标种群数量）
    init_pop_size = cfg.EVO.INIT_POPULATION_SIZE
    # 生成10倍目标种群数量的unimal以确保多样性
    # Create unimal xmls
    p = Pool(cfg.EVO.NUM_PROCESSES)
    timestamp = datetime.now().strftime("%d-%H-%M-%S")
    # 生成unimal_id列表
    idx_unimal_id = [
        (idx, "{}-{}-{}".format(cfg.NODE_ID, idx, timestamp))
        for idx in range(10 * init_pop_size)
    ]
    # 并行创建初始种群unimal
    unimal_ids = p.starmap(globals()[cfg.EVO.INIT_METHOD], idx_unimal_id)

    # 构建相似性图，去除重复unimal
    G = simu.create_graph_from_uids(
        None, unimal_ids, "geom_orientation", graph_type="species"
    )
    # 基于几何方向计算相似性
    # 获取图的连通分量，每个连通分量代表一类相似的unimal
    cc = list(nx.connected_components(G))

    # 从每个连通分量中选择一个unimal保留，保第一个，其他的删除
    unimals_to_remove = []
    unimals_to_keep = []
    for same_unimals in cc:
        if len(same_unimals) == 1:
            unimals_to_keep.extend(list(same_unimals))
            continue
        # 对重复unimal进行排序
        remove_unimals = sorted(
            list(same_unimals),
            key=lambda unimal_id: "-".join(unimal_id.split("-")[:2]),
        )
        # 保留第一个unimal
        unimals_to_keep.append(remove_unimals[0])
        remove_unimals = remove_unimals[1:]
        # 删除其他重复unimal
        unimals_to_remove.extend(remove_unimals)
    # 调整保留的unimal数量以达到初始种群大小
    # Number of unimals to add to achieve init_pop_size.
    padding_count = init_pop_size - len(cc)
    if padding_count > 0:
        random.shuffle(unimals_to_remove)
        unimals_to_remove = unimals_to_remove[padding_count:]
    else:
        random.shuffle(unimals_to_keep)
        unimals_to_remove.extend(unimals_to_keep[init_pop_size:])

    for unimal in unimals_to_remove:
        fu.remove_file(fu.id2path(unimal, "xml"))
        fu.remove_file(fu.id2path(unimal, "unimal_init"))
        fu.remove_file(fu.id2path(unimal, "images"))

    Path(init_setup_done_path).touch()
    print("Finished creating init xmls.")


def kill_pg(p):
    try:
        # 根据进程PID获取其进程组ID
        # 发送SIGTERM信号终止整个进程组
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    # 进程已经结束则忽略异常
    except ProcessLookupError:
        pass

# 重新启动子进程
def relaunch_proc(p, proc_id):
    # Kill the process group
    kill_pg(p)
    # Launch the subproc again
    print("Node ID: {}, proc-id: {} relaunching".format(cfg.NODE_ID, proc_id))
    p = launch_subproc(proc_id)
    return p

# 等待子进程完成或重新启动
def wait_or_kill(subprocs):
    # Main process will wait till we have done search
    while eu.get_searched_space_size() < cfg.EVO.SEARCH_SPACE_SIZE:
        time.sleep(10)  # 10 secs

        # Re-launch subproc if exit was due to error
        new_subprocs = []
        for idx in range(len(subprocs)):
            p, proc_id = subprocs[idx]
            poll = p.poll()

            is_error_path = os.path.join(
                cfg.OUT_DIR, "{}_{}".format(cfg.NODE_ID, p.pid)
            )
            if os.path.exists(is_error_path) or poll:
                fu.remove_file(is_error_path)
                p = relaunch_proc(p, proc_id)

            new_subprocs.append((p, proc_id))

        subprocs = new_subprocs

    if eu.should_save_video():
        video_dir = fu.get_subfolder("videos")
        reg_str = "{}-.*json".format(cfg.NODE_ID)
        while len(fu.get_files(video_dir, reg_str)) > 0:
            time.sleep(60)

    # Ensure that all process will close, dangling process will prevent docker
    # from exiting.
    for p, _ in subprocs:
        kill_pg(p)


# 启动子进程
def launch_subproc(proc_id):
    # 配置文件路径
    cfg_path = os.path.join(cfg.OUT_DIR, cfg.CFG_DEST)
    cmd = "python tools/evo_single_proc.py --cfg {} --proc-id {} NODE_ID {}".format(
        cfg_path, proc_id, cfg.NODE_ID
    )
    # 启动子进程执行evo_single_proc.py脚本
    p = subprocess.Popen(
        cmd, shell=True, executable="/bin/bash", 
        # 为子进程创建新的进程组
        preexec_fn=os.setsid
    )
    return p


# 进化主函数
def evolve():
    # Create initial unimals only in master node
    if cfg.NODE_ID == 0:
        create_init_unimals() # 主节点创建初始种群
    else:
        wait_till_init() # 非主节点等待初始种群创建完成
# cfg.NODE_ID：节点标识符，0表示主节点/控制器
    subprocs = []
    for idx in range(cfg.EVO.NUM_PROCESSES):
        p = launch_subproc(idx)
        subprocs.append((p, idx))

    wait_or_kill(subprocs)
    print("Node ID: {} killed all subprocs!".format(cfg.NODE_ID))


def main():
    # Parse cmd line args
    args = parse_args()

    # Load config options
    cfg.merge_from_file(args.cfg_file)
    cfg.merge_from_list(args.opts)
    # Infer OPTIM.MAX_ITERS
    calculate_max_iters()
    setup_output_dir()
    cfg.freeze()

    # Save the config
    dump_cfg()

    evolve()


if __name__ == "__main__":
    main()
