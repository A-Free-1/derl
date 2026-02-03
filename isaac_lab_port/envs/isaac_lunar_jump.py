"""
Isaac Lab LunarJump 环境

基于 Isaac Lab 框架，实现 lunar_jump 任务。
Compatible with Gymnasium API。
"""

import torch
import numpy as np
from typing import Dict, Tuple, Any
import os


class IsaacLunarJumpEnv:
    """
    MVP 简化版 Isaac Lab LunarJump 环境。
    
    功能：
    - 从 URDF 加载机器人
    - 在月球重力下运行物理仿真
    - 计算 observation（qpos, qvel, imu）
    - 计算 reward（forward + jump + energy）
    - 检测终止条件（跌倒、超时）
    """
    
    def __init__(
        self,
        urdf_path: str,
        num_envs: int = 1,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        task_config: Dict[str, Any] = None,
    ):
        """
        Args:
            urdf_path: 指向 .urdf 文件的路径
            num_envs: 并行环境数（MVP=1，后续可改）
            device: "cuda" 或 "cpu"
            task_config: 任务配置（见 INTERFACE_CONTRACT.md）
        """
        
        self.urdf_path = urdf_path
        self.num_envs = num_envs
        self.device = device
        
        # 默认任务配置
        if task_config is None:
            task_config = {}
        
        self.gravity = task_config.get("gravity", 1.62)  # lunar
        self.dt = task_config.get("dt", 0.01)
        self.max_steps = task_config.get("num_frames", 1000)
        
        reward_scales = task_config.get("reward_scales", {})
        self.forward_scale = reward_scales.get("forward", 1.0)
        self.jump_scale = reward_scales.get("jump", 10.0)
        self.energy_scale = reward_scales.get("energy", 0.001)
        
        # ===== TO DO: Isaac Lab 初始化 =====
        # 你需要在这里用 Isaac Lab API 初始化场景
        # 大概流程是：
        # 1. 创建 Simulation 对象
        # 2. 从 URDF 创建 Actor
        # 3. 设置重力
        # 4. 初始化传感器（contacts, IMU）
        # 
        # 伪代码（实际需要 Isaac Lab 文档）：
        #   from isaac import Simulation, import_asset
        #   self.sim = Simulation()
        #   self.sim.set_gravity([0, 0, -self.gravity])
        #   self.robot = self.sim.import_urdf(urdf_path)
        #   self.sim.initialize()
        
        # 先用占位符
        self.sim = None
        self.robot = None
        
        # Observation / Action space
        # MVP: proprioception only = 4*3 (qpos, qvel) + 3 (imu_angvel) = 15
        self.obs_dim = 15
        self.action_dim = 4  # 4 joints
        
        # 状态缓冲
        self.step_count = torch.zeros(num_envs, device=device, dtype=torch.int32)
        self.torso_height_max = torch.zeros(num_envs, device=device)
        self.torso_height_init = torch.zeros(num_envs, device=device)
        
    def reset(self) -> np.ndarray:
        """
        重置环境。
        
        Returns:
            obs: shape (num_envs, obs_dim) 或 (obs_dim,) if num_envs==1
        """
        
        # ===== TO DO: Isaac Lab 重置 =====
        # self.sim.reset()
        # 设置初始位置/速度
        # 记录初始躯干高度
        
        self.step_count.zero_()
        self.torso_height_max.zero_()
        
        obs = self._compute_obs()
        return obs
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        执行一步仿真。
        
        Args:
            action: shape (num_envs, action_dim) 或 (action_dim,) if num_envs==1
        
        Returns:
            obs: observation
            reward: scalar or (num_envs,)
            terminated: bool or (num_envs,)
            truncated: bool or (num_envs,)
            info: dict with sub-rewards and metrics
        """
        
        # ===== TO DO: Isaac Lab 物理步进 =====
        # 1. 将 action 发送到关节 motor
        # 2. self.sim.step()
        # 3. 计算 obs, reward, terminated
        
        # 暂时用占位符
        obs = self._compute_obs()
        reward = np.array(0.0)
        terminated = False
        truncated = False
        info = {}
        
        self.step_count += 1
        
        # 检查超时
        if self.step_count[0] >= self.max_steps:
            truncated = True
        
        # 计算奖励
        obs, reward_dict = self._compute_reward(action)
        
        # 合并奖励
        reward = (
            self.forward_scale * reward_dict.get("forward", 0.0) +
            self.jump_scale * reward_dict.get("jump", 0.0) -
            self.energy_scale * reward_dict.get("energy", 0.0)
        )
        
        # 构建 info
        info = {
            "__reward__forward": reward_dict.get("forward", 0.0),
            "__reward__jump": reward_dict.get("jump", 0.0),
            "__reward__energy": reward_dict.get("energy", 0.0),
            "jump_height": float(self.torso_height_max[0]) - float(self.torso_height_init[0]),
            "metric": float(self.torso_height_max[0]) - float(self.torso_height_init[0]),
        }
        
        return obs, reward, terminated, truncated, info
    
    def _compute_obs(self) -> np.ndarray:
        """
        计算观测（proprioception）。
        
        Returns:
            obs: shape (obs_dim,)
                [qpos_0, qpos_1, qpos_2, qpos_3, 
                 qvel_0, qvel_1, qvel_2, qvel_3,
                 imu_angvel_x, imu_angvel_y, imu_angvel_z,
                 ...pad to obs_dim]
        """
        
        # ===== TO DO: 从 Isaac Lab 读取 state =====
        # qpos = self.robot.get_joint_angles()
        # qvel = self.robot.get_joint_velocities()
        # angvel = self.robot.get_angular_velocity()
        
        # 暂时返回全 0
        obs = np.zeros(self.obs_dim, dtype=np.float32)
        return obs
    
    def _compute_reward(self, action: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        计算奖励分量。
        
        Returns:
            obs: observation (再算一遍以确保一致性)
            reward_dict: {"forward": ..., "jump": ..., "energy": ...}
        """
        
        # ===== TO DO: 从 Isaac Lab 读取 kinematics =====
        # torso_pos = self.robot.get_link_position("torso/0")
        # torso_vel = self.robot.get_link_velocity("torso/0")
        
        # 暂时返回占位符
        reward_dict = {
            "forward": 0.0,   # 前向速度
            "jump": 0.0,      # 跳跃高度
            "energy": 0.1,    # 能量消耗（action 的平方和）
        }
        
        obs = self._compute_obs()
        return obs, reward_dict
    
    def close(self):
        """清理资源。"""
        if self.sim is not None:
            self.sim.close()


# ============ 测试代码 ============

if __name__ == "__main__":
    # 简单的 MVP 测试
    urdf_path = "/home/t/yb/agrimgupta_derl/derl/isaac_lab_port/assets/simple_robot.urdf"
    
    env = IsaacLunarJumpEnv(
        urdf_path=urdf_path,
        num_envs=1,
        task_config={
            "gravity": 1.62,
            "num_frames": 100,
            "reward_scales": {"forward": 1.0, "jump": 10.0, "energy": 0.001},
        }
    )
    
    # 重置
    obs = env.reset()
    print(f"Obs shape: {obs.shape}")
    print(f"Obs sample: {obs[:5]}")
    
    # 步进
    for _ in range(10):
        action = np.random.uniform(-1, 1, env.action_dim)
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Reward: {reward:.4f}, JumpHeight: {info['jump_height']:.4f}")
