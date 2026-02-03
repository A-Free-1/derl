# MVP 执行清单（分步指南）

> 你现在有了所有的骨架代码。这份文档告诉你"接下来要干什么"。

---

## 前置条件检查清单

在开始 MVP 之前，先确认你有这些环境：

- [ ] **Isaac Lab 已安装**
  ```bash
  # 如果还没装，按 Isaac Lab 官方教程安装
  # https://docs.isaacsim.omniverse.nvidia.com/
  pip install isaaclab
  ```

- [ ] **CUDA 环境**
  ```bash
  nvidia-smi  # 应该能看到 GPU 信息
  ```

- [ ] **PyTorch GPU 版本**
  ```bash
  python -c "import torch; print(torch.cuda.is_available())"  # 应该输出 True
  ```

- [ ] **仓库中已有新目录**
  ```
  isaac_lab_port/
  ├── MVP_README.md
  ├── INTERFACE_CONTRACT.md
  ├── envs/
  │   └── isaac_lunar_jump.py
  ├── assets/
  │   └── simple_robot.urdf
  └── trainer/
  ```

---

## Step 0：验证 URDF 文件（5 分钟）

```bashco
# 检查 simple_robot.urdf 是否存在且有效
cd /home/t/yb/agrimgupta_derl/derl

# 用 urdf-parser-py 验证 URDF 语法
python -c "
from urdf_parser_py.urdf import URDF
robot = URDF.from_file('isaac_lab_port/assets/simple_robot.urdf')
print(f'Robot name: {robot.name}')
print(f'Num links: {len(robot.links)}')
print(f'Num joints: {len(robot.joints)}')
"

# 应该输出：
# Robot name: unimal_mvp_simple
# Num links: 5
# Num joints: 4
```

如果出错，检查 URDF 文件的 XML 语法。

---

## Step 1：用 Isaac Lab 加载 URDF（15-30 分钟）

现在你需要**真正用 Isaac Lab API 来填补 `TO DO`**。

在 `isaac_lab_port/envs/isaac_lunar_jump.py` 的 `__init__` 方法，你需要做：

```python
# 伪代码（实际需要查 Isaac Lab 文档）

from isaac import Simulation, Usd
from isaac_sim.sim_utils import SimulationCfg, PhysicsMaterialCfg

# 创建模拟器
sim_cfg = SimulationCfg()
self.sim = Simulation(sim_cfg)

# 导入 URDF
from_import_cfg = UsdFileCfg(
    usd_path=urdf_path,
    replicate_physics=True,  # 如果 num_envs > 1
    scale=1.0,
)
self.robot = self.sim.import_actor(from_import_cfg)

# 设置重力
self.sim.set_gravity([0, 0, -self.gravity])

# 初始化
self.sim.initialize()

# 初始化传感器（joint state, imu, contact）
# ...
```

> **提示**：查看 Isaac Lab 官方教程 `https://github.com/isaac-sim/IsaacLab`，找到类似的 robot loading 例子。

---

## Step 2：实现 `reset()` 和 `step()` （30-60 分钟）

填补 `_compute_obs()` 和 `_compute_reward()` 中的 `TO DO`。

关键 API（参考 Isaac Lab 文档）：

```python
# 获取关节角度和速度
qpos = self.robot.data.joint_pos  # shape: (num_envs, num_joints)
qvel = self.robot.data.joint_vel  # shape: (num_envs, num_joints)

# 获取躯干信息
torso_pos = self.robot.data.body_pos_w[:, 0, :]  # body 0 = torso
torso_vel = self.robot.data.body_lin_vel_w[:, 0, :]

# 获取角速度（如果有 IMU sensor）
imu_angvel = self.robot.data.imu_angular_vel

# 设置关节控制力
self.robot.data.joint_effort[:] = action * joint_strength
```

---

## Step 3：运行 MVP 脚本（5-10 分钟）

一旦环境的 `__init__`, `reset()`, `step()` 都实现了，就可以试运行：

```bash
python run_mvp_lunar_jump.py \
  --urdf isaac_lab_port/assets/simple_robot.urdf \
  --num-epochs 100 \
  --steps-per-epoch 100 \
  --device cuda
```

预期输出（30 分钟内应该看到）：

```
[MVP] Initializing environment...
  URDF: isaac_lab_port/assets/simple_robot.urdf
  Device: cuda
[MVP] Environment created. Obs dim: 15, Action dim: 4
[MVP] Starting training (100 epochs)...

[PPO] Epoch 10/100 | Avg Return: 0.3214 | Avg Jump Height: 0.0520
[PPO] Epoch 20/100 | Avg Return: 0.8934 | Avg Jump Height: 0.1245
[PPO] Epoch 30/100 | Avg Return: 2.3451 | Avg Jump Height: 0.2890
...
[PPO] Training finished!
Final avg return: 45.6234
Final avg jump height: 0.5812
```

---

## 常见问题排查

### Q1：`Error: URDF file not found`
- 检查 URDF 路径是否正确
- 运行 `ls -la isaac_lab_port/assets/simple_robot.urdf` 确认文件存在

### Q2：Isaac Lab 导入失败（`ModuleNotFoundError: No module named 'isaac'`）
- Isaac Lab 没有安装好
- 按官方教程重新安装

### Q3：`NaN` 出现在 reward 或 obs 中
- 可能是初始条件不对（如机器人穿过地面）
- 调整 `simple_robot.urdf` 中的初始位置
- 或检查物理参数（mass/inertia）是否合理

### Q4：reward 一直是负数或 0
- jump_height 计算有问题
- 检查 `_compute_reward()` 中是否正确读取了躯干高度
- 或 reward scale 的权重设置（见 INTERFACE_CONTRACT.md）

### Q5：很快就 episode terminated，没有时间跳跃
- 终止条件过于严格
- 调整 `_compute_reward()` 中的"跌倒"判断逻辑
- 或增加 `max_steps` 参数

---

## MVP 成功的标志

✅ 当你看到这样的日志，MVP 就成功了：

```
[PPO] Epoch 50/100 | Avg Return: 3.5678 | Avg Jump Height: 0.35
```

即：
1. 环境正常加载（没有 NaN 或崩溃）
2. reward > 0（证明学到了有用的行为）
3. jump_height 在增加（证明学到了跳跃）

---

## 下一步（完成 MVP 后）

一旦 MVP 跑通，你就可以进入**阶段 B**（接通构型生成器）。

现在的 `isaac_lab_port/INTERFACE_CONTRACT.md` 已经明确了：
- genotype dict 的格式
- URDF 的要求
- fitness 输出的格式

所以下一步就是：
1. 从 `SymmetricUnimal` 抽象出 `Genotype` 类
2. 实现 `genotype_to_urdf()` 转换器
3. 批量生成 50–100 个构型，验证可加载率 >= 95%

---

## 时间预估

- 前置条件检查：5 分钟
- Step 0（URDF 验证）：5 分钟
- Step 1（Isaac 加载）：15–30 分钟（取决于文档）
- Step 2（实现 reset/step）：30–60 分钟
- Step 3（运行脚本）：5–10 分钟
- **总计：1–2 小时**

如果遇到问题卡住，可以给我截图或错误信息，我帮你排查。

---

## 文件清单（现在你已有）

```
/home/t/yb/agrimgupta_derl/derl/
├── ISAAC_LAB_MIGRATION_GUIDE.md
├── run_mvp_lunar_jump.py
└── isaac_lab_port/
    ├── MVP_README.md
    ├── INTERFACE_CONTRACT.md
    ├── envs/
    │   └── isaac_lunar_jump.py
    ├── assets/
    │   └── simple_robot.urdf
    └── trainer/
```

现在开始 Step 0 吧！
