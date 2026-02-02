import numpy as np
from gym import utils

from derl.config import cfg
from derl.envs.modules.agent import Agent
from derl.envs.modules.floor import Floor
from derl.envs.modules.terrain import Terrain
from derl.envs.tasks.unimal import UnimalEnv
from derl.envs.wrappers.hfield import AvoidWallReward
from derl.envs.wrappers.hfield import HfieldObs1D
from derl.envs.wrappers.hfield import HfieldObs2D
from derl.envs.wrappers.hfield import StandReward
from derl.envs.wrappers.hfield import TerminateOnFalling
from derl.envs.wrappers.hfield import TerminateOnRotation
from derl.envs.wrappers.hfield import TerminateOnTerrainEdge
from derl.envs.wrappers.hfield import TerminateOnWallContact
from derl.envs.wrappers.hfield import UnimalHeightObs


class LunarJumpTask(UnimalEnv, utils.EzPickle):
    """
    Lunar Jumping Robot Task
    
    Objective: Maximize jumping height and horizontal distance on lunar surface
    - Gravity: 1.62 m/s² (1/6 of Earth's gravity)
    - Rewards: jump_height (weighted heavy) + horizontal_distance + energy_penalty
    """
    
    def __init__(self, xml_str, unimal_id):
        UnimalEnv.__init__(self, xml_str, unimal_id)
        
        # Store initial torso height for jump height calculation
        self.reset_torso_height = None
        self.torso_height_max = 0.0
        
    ###########################################################################
    # Lunar Jump Metrics
    ###########################################################################
    
    def _calculate_jump_height(self):
        """Calculate maximum jump height from reset position"""
        current_height = self.sim.data.get_body_xpos("torso/0")[2]
        
        # Track maximum height during this episode
        if current_height > self.torso_height_max:
            self.torso_height_max = current_height
        
        # Jump height = current height - reset height
        jump_height = self.torso_height_max - self.reset_torso_height
        return max(0.0, jump_height)
    
    def _calculate_horizontal_distance(self, xy_pos_before, xy_pos_after):
        """Calculate horizontal distance traveled in this step"""
        xy_vel = (xy_pos_after - xy_pos_before) / self.dt
        distance = np.linalg.norm(xy_vel)
        return distance
    
    ###########################################################################
    # Sim step and reset
    ###########################################################################
    
    def step(self, action):
        """
        Step function with lunar jumping rewards
        
        Reward components:
        1. forward_reward: horizontal distance traveled (weight: 1.0)
        2. jump_reward: maximum height achieved (weight: configurable)
        3. ctrl_cost: energy cost of actions (penalty)
        """
        if cfg.HFIELD.DIM == 1:
            info, forward_reward, jump_height = self.step_1d(action)
        else:
            info, forward_reward, jump_height = self.step_2d(action)
        
        ctrl_cost = self.control_cost(action)
        
        # Lunar jumping composite reward
        jump_reward = cfg.ENV.JUMP_REWARD_WEIGHT * jump_height
        energy_cost = cfg.ENV.ENERGY_COST_WEIGHT * self.calculate_energy()
        
        reward = forward_reward + jump_reward - ctrl_cost - energy_cost
        observation = self._get_obs()
        
        info_ = {
            "__reward__ctrl": ctrl_cost,
            "__reward__energy": self.calculate_energy(),
            "__reward__forward": forward_reward,
            "__reward__jump": jump_reward,
            "jump_height": jump_height,
            "max_jump_height": self.torso_height_max - self.reset_torso_height,
        }
        info.update(info_)
        
        return observation, reward, False, info
    
    def step_1d(self, action):
        """1D locomotion (left-right on flat terrain)"""
        x_pos_before = self.sim.data.qpos[0]
        self.do_simulation(action)
        x_pos_after = self.sim.data.qpos[0]
        
        x_vel = (x_pos_after - x_pos_before) / self.dt
        forward_reward = cfg.ENV.FORWARD_REWARD_WEIGHT * x_vel
        
        jump_height = self._calculate_jump_height()
        
        pos_info = {
            "x_pos": x_pos_after,
            "x_vel": x_vel,
        }
        return pos_info, forward_reward, jump_height
    
    def step_2d(self, action):
        """2D locomotion (forward movement on terrain)"""
        xy_pos_before = self.sim.data.get_body_xpos("torso/0")[:2].copy()
        self.do_simulation(action)
        xy_pos_after = self.sim.data.get_body_xpos("torso/0")[:2].copy()
        
        xy_vel = (xy_pos_after - xy_pos_before) / self.dt
        x_vel, y_vel = xy_vel
        
        forward_reward = cfg.ENV.FORWARD_REWARD_WEIGHT * x_vel
        jump_height = self._calculate_jump_height()
        
        pos_info = {
            "x_pos": xy_pos_after[0],
            "x_vel": x_vel,
            "xy_pos_before": xy_pos_before,
            "xy_pos_after": xy_pos_after,
            "metric": xy_pos_after[0],  # For ranking/selection
        }
        return pos_info, forward_reward, jump_height
    
    def reset(self):
        """Reset episode and initialize jump height tracking"""
        obs = super().reset()
        
        # Initialize jump height tracking
        self.reset_torso_height = self.sim.data.get_body_xpos("torso/0")[2]
        self.torso_height_max = self.reset_torso_height
        
        return obs


def make_env_lunar_jump(xml, unimal_id):
    """Factory function for lunar jumping environment"""
    env = LunarJumpTask(xml, unimal_id)
    
    # Add modules
    for module in cfg.ENV.MODULES:
        env.add_module(globals()[module])
    
    # Reset is needed to setup observation spaces, sim etc which might be
    # needed by wrappers
    env.reset()
    
    # Add all wrappers
    env = UnimalHeightObs(env)
    env = StandReward(env)
    env = TerminateOnFalling(env)
    
    if "Terrain" in cfg.ENV.MODULES:
        if cfg.HFIELD.DIM == 1:
            env = HfieldObs1D(env)
        else:
            env = HfieldObs2D(env)
            env = TerminateOnTerrainEdge(env)
        
        if "AvoidWallReward" in cfg.ENV.WRAPPERS:
            env = AvoidWallReward(env)
        if "TerminateOnWallContact" in cfg.ENV.WRAPPERS:
            env = TerminateOnWallContact(env)
    
    if "TerminateOnRotation" in cfg.ENV.WRAPPERS:
        env = TerminateOnRotation(env)
    
    return env
