import os
import random

import numpy as np

from derl.config import cfg
from derl.utils import file as fu


# From: https://github.com/QUVA-Lab/artemis/blob/peter/artemis/general/pareto_efficiency.py
def is_pareto_efficient(costs, return_mask=True):
    """
    Find the pareto-efficient points
    :param costs: An (n_points, n_costs) array
    :param return_mask: True to return a mask
    :return: An array of indices of pareto-efficient points.
        If return_mask is True, this will be an (n_points, ) boolean array
        Otherwise it will be a (n_efficient_points, ) integer array of indices.
    """
    is_efficient = np.arange(costs.shape[0])
    n_points = costs.shape[0]
    next_point_index = 0  # Next index in the is_efficient array to search for
    while next_point_index < len(costs):
        nondominated_point_mask = np.any(costs < costs[next_point_index], axis=1)
        nondominated_point_mask[next_point_index] = True
        is_efficient = is_efficient[
            nondominated_point_mask
        ]  # Remove dominated points
        costs = costs[nondominated_point_mask]
        next_point_index = np.sum(nondominated_point_mask[:next_point_index]) + 1
    if return_mask:
        is_efficient_mask = np.zeros(n_points, dtype=bool)
        is_efficient_mask[is_efficient] = True
        return is_efficient_mask
    else:
        return is_efficient


def select_parent():
    if "aging" in cfg.EVO.TOURNAMENT_TYPE:
        return aging_tournament()
    if "vanilla" in cfg.EVO.TOURNAMENT_TYPE:
        return vanilla_tournament()


def get_dominate_mask(metadatas):
    rew_keys = cfg.EVO.SELECTION_CRITERIA
    rews = []
    for m in metadatas:
        rews.append([m[rew_key] for rew_key in rew_keys])

    dominate_mask = is_pareto_efficient(
        cfg.EVO.SELECTION_CRITERIA_OBJ * np.asarray(rews)
    )
    return dominate_mask


def aging_tournament():
    # 获取metadata文件夹中的所有JSON文件路径
    metadata_paths = fu.get_files(fu.get_subfolder("metadata"), ".*json")
    # 按修改时间排序
    metadata_paths = sorted(metadata_paths, key=os.path.getmtime)
    # 只保留最近的AGING_WINDOW_SIZE个unimals
    metadata_paths = metadata_paths[-cfg.EVO.AGING_WINDOW_SIZE :]

    num_unimals = cfg.EVO.NUM_PARTICIPANTS

    if "percent" in cfg.EVO.TOURNAMENT_TYPE:
        num_unimals = int(
            (cfg.EVO.PERCENT_PARTICIPANTS / 100) * cfg.EVO.AGING_WINDOW_SIZE
        )
        num_unimals = max(2, num_unimals)

    # 从最近的unimals中随机选择num_unimals个进行锦标赛
    metadata_paths = random.choices(metadata_paths, k=num_unimals)
    # 加载对应的metadata
    metadatas = [fu.load_json(m) for m in metadata_paths]

    # 计算支配掩码
    dominate_mask = get_dominate_mask(metadatas)
    # 获取帕累托前沿的unimals
    pareto_front = [m for m, d_mask in zip(metadatas, dominate_mask) if d_mask]
    # 如果所有unimals都被支配，则随机选择一个返回
    if np.all(dominate_mask):
        # No solutions dominates all. Choose at random and return
        return random.choice(metadatas)
    # 否则，从帕累托前沿中随机选择一个返回
    else:
        # Return a random unimal from the pareto_front
        return random.choice(pareto_front)

# 锦标赛选择（无年龄机制）
def vanilla_tournament():
    metadata_paths = fu.get_files(fu.get_subfolder("metadata"), ".*json")

    num_unimals = cfg.EVO.NUM_PARTICIPANTS

    if "percent" in cfg.EVO.TOURNAMENT_TYPE:
        num_unimals = int(
            (cfg.EVO.PERCENT_PARTICIPANTS / 100) * len(metadata_paths)
        )
        num_unimals = max(2, num_unimals)

    metadata_paths = random.choices(metadata_paths, k=num_unimals)
    metadatas = [fu.load_json(m) for m in metadata_paths]

    dominate_mask = get_dominate_mask(metadatas)
    pareto_front = [m for m, d_mask in zip(metadatas, dominate_mask) if d_mask]
    if np.all(dominate_mask):
        # No solutions dominates all. Choose at random and return
        return random.choice(metadatas)
    else:
        # Return a random unimal from the pareto_front and remove a random
        # unimal which is dominated.
        for path, d_mask in zip(metadata_paths, dominate_mask):
            if not d_mask:
                fu.remove_file(path)
                break
        return random.choice(pareto_front)


def get_parent_id(child_id):
    child_init = fu.load_pickle(fu.id2path(child_id, "unimal_init"))
    return child_init["parent_id"]


def get_searched_space_size():
    """Returns total number of unimals generated so far."""
    return len(os.listdir(fu.get_subfolder("models")))


def get_population_size():
    """Return the current population size."""
    return len(os.listdir(fu.get_subfolder("metadata")))


def should_save_video():
    """Return if video of unimal has to be saved."""
    # In case of RGS don't save video
    # 当前不是进化搜索则不保存视频
    if not cfg.EVO.IS_EVO:
        return False

    num_searched = get_searched_space_size()

    if "aging" in cfg.EVO.TOURNAMENT_TYPE:
        pop_size = cfg.EVO.AGING_WINDOW_SIZE
    elif "vanilla" in cfg.EVO.TOURNAMENT_TYPE:
        return False

    if num_searched > (cfg.EVO.SEARCH_SPACE_SIZE - pop_size):
        return True
    else:
        return False


def get_metadata_paths(metadata_dir=None):
    # 获取metadata文件夹中的所有JSON文件路径
    if metadata_dir is None:
        metadata_dir = fu.get_subfolder("metadata")
    metadata_paths = fu.get_files(
        metadata_dir, ".*json", sort=True, sort_type="time"
    )
    if cfg.EVO.IS_EVO and "aging" in cfg.EVO.TOURNAMENT_TYPE:
        metadata_paths = metadata_paths[-cfg.EVO.AGING_WINDOW_SIZE :]
    return metadata_paths

