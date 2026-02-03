# DERL Isaac Lab 迁移 - 数据格式契约

> 这个文档定义了 **genotype → asset → env → fitness** 的完整数据流。
> 
> 目的：让 MVP / 阶段 B / 阶段 C 可以清晰地相互配合，无需大量改代码。

---

## 1. Genotype（构型基因）数据结构

构型的"遗传信息"用 Python dict 表示：

```python
genotype = {
    "id": "0-1234-31-12-34-56",  # unique identifier
    "topology": {
        # 树结构：body name → 其 children
        "torso/0": {
            "children": ["limb/0", "limb/1"],
            "limbs": {
                "limb/0": {
                    "site_name": "torso/0/top",
                    "geometry": {
                        "radius": 0.05,
                        "height": 0.15,
                    },
                    "joint_params": {
                        "range": [-1.57, 1.57],  # rad
                        "damping": 0.1,
                        "frictionloss": 0.0,
                    },
                    "actuator_params": {
                        "gear": 100.0,
                        "ctrlrange": [-1.0, 1.0],
                    },
                    "density": 1000.0,  # kg/m^3
                },
                "limb/1": { ... },
            }
        }
    },
    "body_params": {
        "torso_density": 1000.0,
        "limb_density": 800.0,
        "gravity": 1.62,  # for lunar_jump
    }
}
```

> **注意**：这个结构应该从 `derl/envs/morphology.py::SymmetricUnimal` 里"解耦"出来。
> MVP 阶段只用手工的 genotype；阶段 B 时，SymmetricUnimal.mutate() 输出这个结构。

---

## 2. Asset（资产）格式

### 2.1 URDF 文件路径约定

```
isaac_lab_port/assets/
├── <genotype_id>.urdf          # 自动生成，对应一个 genotype
├── simple_robot.urdf           # MVP 用的硬编码模板
└── README.md
```

### 2.2 URDF 的内容要求

```xml
<?xml version="1.0" ?>
<robot name="unimal_<id>">
  <!-- 动力学参数必须有 -->
  <link name="torso/0">
    <inertial>
      <mass value="0.5"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>
    </inertial>
    <collision>
      <geometry><box size="0.2 0.2 0.1"/></geometry>
    </collision>
  </link>
  
  <!-- 关节必须有 limit / damping / friction -->
  <joint name="limb/0_joint" type="revolute">
    <axis xyz="0 1 0"/>
    <limit effort="10" velocity="5" lower="-1.57" upper="1.57"/>
    <dynamics damping="0.1" friction="0.0"/>
    ...
  </joint>
  
  <!-- actuator / transmission（可选，但推荐有） -->
  <transmission name="limb/0_trans">
    <type>transmission_interface/SimpleTransmission</type>
    <joint name="limb/0_joint">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
    </joint>
    <actuator name="limb/0_motor">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
      <mechanicalReduction>100</mechanicalReduction>
    </actuator>
  </transmission>
</robot>
```

---

## 3. Environment（环境）接口

Isaac Lab 环境应该遵循这个接口（类似 Gymnasium）：

```python
class IsaacLunarJumpEnv:
    
    def __init__(self, urdf_path: str, task_config: dict):
        """
        Args:
            urdf_path: 指向 .urdf 文件的路径
            task_config: 任务配置，见下面的 task_config_schema
        """
        self.observation_space = gym.spaces.Box(...)  # shape (obs_dim,)
        self.action_space = gym.spaces.Box(...)       # shape (action_dim,)
        
    def reset(self):
        """
        Returns:
            obs: shape (obs_dim,) 或 (num_envs, obs_dim) 如果 vectorized
        """
        
    def step(self, action):
        """
        Args:
            action: shape (action_dim,) 或 (num_envs, action_dim)
        
        Returns:
            obs: observation
            reward: float or (num_envs,) 如果 vectorized
            terminated: bool or (num_envs,)
            truncated: bool or (num_envs,)
            info: dict，包含：
                - "__reward__forward": float（forward 子奖励）
                - "__reward__jump": float（jump 子奖励）
                - "__reward__energy": float（能量惩罚）
                - "jump_height": float（最大跳跃高度）
                - "metric": float（主要评价指标，e.g., jump_height）
                ...
        """
```

### task_config_schema

```python
task_config = {
    "gravity": 1.62,  # lunar gravity
    "dt": 0.01,       # simulation timestep (s)
    "num_envs": 1,    # for MVP, 1; later can be 256/512
    "num_frames": 1000,  # max steps per episode
    
    # Reward weights
    "reward_scales": {
        "forward": 1.0,
        "jump": 10.0,
        "energy": 0.001,
    },
    
    # Other task-specific params
    "obs_scales": {
        "lin_vel": 1.0,
        "ang_vel": 1.0,
    },
}
```

---

## 4. Fitness Output（适应度输出）

训练完后，返回这个字典给进化算法：

```python
fitness = {
    "id": genotype["id"],
    
    # 各奖励分量（平均最后 100 episodes）
    "__reward__forward": 12.5,
    "__reward__jump": 23.4,
    "__reward__energy": -0.8,
    
    # 最终平均奖励
    "reward": 35.1,
    
    # 任务特定的 metric（如 jump_height）
    "metric": 0.58,  # 最大跳跃高度（米）
    
    # Lineage（从哪个父代进化来）
    "parent_id": "0-1200-...",  # None if initial pop
    "mutation_op": "grow_limb",  # 最后一次变异操作
    
    # 训练过程元数据
    "training_steps": 500000,
    "training_time_sec": 1200,
    "converged": True,
}
```

---

## 5. Evolution Loop 中的数据流

```
┌─────────────────┐
│  Genotype Pool  │  (metadata 落盘: output/metadata/*.json)
└────────┬────────┘
         │
         ├─► select_parent()  ◄─── 从 fitness 的 Pareto front 选
         │
         │
    ┌────▼─────┐
    │  Mutate   │  ◄─── SymmetricUnimal.mutate() 生成新 genotype
    └────┬─────┘
         │
    ┌────▼──────────────┐
    │ Genotype → URDF   │  ◄─── genotype_to_urdf(genotype)
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │  Isaac Env + PPO  │  ◄─── train(urdf_path, task_config) → fitness
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │  Fitness Output   │  ◄─── 写回 metadata（覆盖或新增）
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │  Check Stop Cond  │  ◄─── if searched_size >= SEARCH_SPACE_SIZE: break
    └───────────────────┘
```

---

## 6. MVP 阶段数据流（简化版）

MVP 不涉及进化，只是：

```
Hard-coded genotype
       │
       ▼
Simple robot.urdf（手工）
       │
       ▼
Isaac LunarJump Env
       │
       ▼
PPO Train 30 min
       │
       ▼
Print reward curve ✓
```

---

## 7. 阶段 B 数据流（接通构型生成）

```
SymmetricUnimal.mutate()
       │
       ▼
genotype dict
       │
       ▼
genotype_to_urdf(genotype)  ◄─── 新函数
       │
       ▼
<id>.urdf
       │
       ▼
Isaac Env + PPO Train
       │
       ▼
fitness dict → output/metadata/<id>.json
```

---

## 8. 阶段 C 数据流（完整进化）

```
Evolution Loop
    │
    ├─ select_parent()  ◄─── derl/utils/evo.py（保留）
    │
    ├─ SymmetricUnimal.mutate()  ◄─── 输出 genotype dict
    │
    ├─ genotype_to_urdf()  ◄─── 阶段 B 的函数
    │
    ├─ Isaac Env + PPO  ◄─── 阶段 A/B 的环境
    │
    ├─ fitness → metadata  ◄─── 保留写盘逻辑
    │
    └─ 循环 4000 次，写 Pareto front
```

---

## 9. 文件路径约定

为了让三个阶段无缝接上，约定这样的路径：

```
isaac_lab_port/
├── assets/
│   ├── simple_robot.urdf          # MVP 硬编码
│   └── <genotype_id>.urdf         # 阶段 B/C 自动生成
├── envs/
│   ├── isaac_lunar_jump.py        # 环境实现
│   └── ...
├── trainer/
│   └── ppo_trainer_stub.py        # 训练封装
├── genotype.py                    # Genotype 类（阶段 B 新增）
├── genotype_to_urdf.py            # 转换函数（阶段 B 新增）
└── evolution_isaac.py             # 进化循环（阶段 C 新增）
```

---

## 10. 检查清单（你按这个对上就行）

MVP 完成后检查：

- [ ] `isaac_lab_port/assets/simple_robot.urdf` 存在且可加载
- [ ] `isaac_lab_port/envs/isaac_lunar_jump.py` 的 env 能 reset/step
- [ ] `reset()` 返回 obs，shape = (obs_dim,)
- [ ] `step(action)` 返回 (obs, reward, terminated, truncated, info)
- [ ] info 中包含 "__reward__jump"、"metric" 等字段
- [ ] PPO 训练 30 min 后 reward > 0

阶段 B 完成后检查：

- [ ] `genotype_to_urdf()` 能批量生成 URDF（100 个都不崩）
- [ ] 生成的 URDF 都能加载到 Isaac Env
- [ ] 可加载率 >= 95%

阶段 C 完成后检查：

- [ ] Evolution loop 能跑 500 代不停
- [ ] metadata 正常写盘（每个构型 1 个 .json）
- [ ] Pareto front 正常更新

---

## Q & A

**Q1：为什么要定这个契约？**
A：避免三个阶段之间改来改去。MVP 专注"环境 + 训练"，阶段 B 专注"构型生成"，阶段 C 专注"进化调度"。

**Q2：MVP 的 simple_robot.urdf 怎么来？**
A：可以手工写（参考下面的模板），也可以从现有 MuJoCo xml 转换。我会给转换脚本。

**Q3：fitness dict 的各字段都是必需吗？**
A：核心字段（id、reward、metric、parent_id）必需。其他可选（如 training_steps）。

**Q4：genotype dict 和 fitness dict 是不同的吗？**
A：是的。genotype 是"输入"（怎么构建这个机器人），fitness 是"输出"（这个机器人的表现如何）。
