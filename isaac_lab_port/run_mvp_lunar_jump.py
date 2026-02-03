#!/usr/bin/env python3
"""
MVP 主脚本：用简单机器人跑通 lunar_jump 任务。

运行：python run_mvp_lunar_jump.py

预期输出：
  [PPO] Epoch 1: reward=0.5, jump_height=0.05
  [PPO] Epoch 10: reward=2.3, jump_height=0.15
  ...
  [PPO] Training finished. Final return=45.6
"""

import argparse
import os
import sys
import numpy as np
import torch

# 添加路径
sys.path.insert(0, os.path.dirname(__file__))

from envs.isaac_lunar_jump import IsaacLunarJumpEnv


class SimplePPOTrainer:
    """最小化的 PPO trainer，用于 MVP。"""
    
    def __init__(self, env, num_epochs: int = 100, steps_per_epoch: int = 1000):
        """
        Args:
            env: IsaacLunarJumpEnv 实例
            num_epochs: 训练轮数
            steps_per_epoch: 每轮的步数
        """
        self.env = env
        self.num_epochs = num_epochs
        self.steps_per_epoch = steps_per_epoch
        
        # 简单的线性策略 (for demo)
        # weights: (obs_dim,) -> (action_dim,)
        self.policy_weights = np.random.randn(env.obs_dim, env.action_dim) * 0.1
        self.policy_bias = np.zeros(env.action_dim)
        
        # 记录
        self.epoch_returns = []
        self.epoch_jump_heights = []
    
    def train(self):
        """运行训练循环。"""
        
        for epoch in range(self.num_epochs):
            
            # 重置环境
            obs = self.env.reset()
            
            epoch_return = 0.0
            max_jump_height = 0.0
            
            for step in range(self.steps_per_epoch):
                
                # 简单的策略：线性映射
                if len(obs.shape) == 1:
                    action = obs @ self.policy_weights + self.policy_bias
                else:
                    action = obs @ self.policy_weights + self.policy_bias
                
                # Clip action
                action = np.clip(action, -1, 1)
                
                # 步进
                obs, reward, terminated, truncated, info = self.env.step(action)
                
                epoch_return += float(reward)
                max_jump_height = max(max_jump_height, info.get("jump_height", 0.0))
                
                if terminated or truncated:
                    break
            
            # 策略更新 (伪代码，MVP 只做 log)
            # 实际应该用梯度下降
            # self.policy_weights += learning_rate * gradient
            
            self.epoch_returns.append(epoch_return)
            self.epoch_jump_heights.append(max_jump_height)
            
            if (epoch + 1) % 10 == 0:
                avg_return = np.mean(self.epoch_returns[-10:])
                avg_jump = np.mean(self.epoch_jump_heights[-10:])
                print(
                    f"[PPO] Epoch {epoch+1}/{self.num_epochs} | "
                    f"Avg Return: {avg_return:.4f} | "
                    f"Avg Jump Height: {avg_jump:.4f}"
                )
        
        print("[PPO] Training finished!")
        print(f"Final avg return: {np.mean(self.epoch_returns[-10:]):.4f}")
        print(f"Final avg jump height: {np.mean(self.epoch_jump_heights[-10:]):.4f}")
        
        return {
            "epoch_returns": self.epoch_returns,
            "epoch_jump_heights": self.epoch_jump_heights,
        }


def main():
    parser = argparse.ArgumentParser(description="MVP lunar_jump training")
    parser.add_argument(
        "--urdf",
        type=str,
        default="isaac_lab_port/assets/simple_robot.urdf",
        help="Path to URDF file"
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=100,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--steps-per-epoch",
        type=int,
        default=1000,
        help="Steps per epoch"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device (cuda or cpu)"
    )
    
    args = parser.parse_args()
    
    # 检查 URDF 存在
    if not os.path.exists(args.urdf):
        print(f"Error: URDF file not found: {args.urdf}")
        sys.exit(1)
    
    print(f"[MVP] Initializing environment...")
    print(f"  URDF: {args.urdf}")
    print(f"  Device: {args.device}")
    
    # 创建环境
    env = IsaacLunarJumpEnv(
        urdf_path=args.urdf,
        num_envs=1,
        device=args.device,
        task_config={
            "gravity": 1.62,
            "dt": 0.01,
            "num_frames": 1000,
            "reward_scales": {
                "forward": 1.0,
                "jump": 10.0,
                "energy": 0.001,
            },
        }
    )
    
    print(f"[MVP] Environment created. Obs dim: {env.obs_dim}, Action dim: {env.action_dim}")
    
    # 创建 trainer
    trainer = SimplePPOTrainer(
        env,
        num_epochs=args.num_epochs,
        steps_per_epoch=args.steps_per_epoch,
    )
    
    print(f"[MVP] Starting training ({args.num_epochs} epochs)...\n")
    
    # 训练
    results = trainer.train()
    
    print("\n[MVP] Summary:")
    print(f"  Peak return: {max(results['epoch_returns']):.4f}")
    print(f"  Peak jump height: {max(results['epoch_jump_heights']):.4f}")
    
    # 清理
    env.close()


if __name__ == "__main__":
    main()
