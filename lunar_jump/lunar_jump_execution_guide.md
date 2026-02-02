# 🚀 月面跳跃机器人 - 执行指南

## 📊 关于 `python tools/evolution.py --cfg configs/evo/lunar_jump.yml`

### **是否显示可视化MuJoCo界面？**

**答案：❌ 默认情况下不显示可视化界面**

这个命令会执行**纯后台训练**，不会弹出MuJoCo可视化窗口。

---

## 🔍 执行流程详解

### **1️⃣ 命令执行流程**
```
python tools/evolution.py --cfg configs/evo/lunar_jump.yml
                    ↓
        [主进程 - evolution.py]
        初始化种群 (NODE_ID=0为主节点)
                    ↓
        并行启动多个子进程
        (默认 cfg.EVO.NUM_PROCESSES 个)
                    ↓
        [子进程 - evo_single_proc.py] × N
        每个子进程训练一个Unimal
                    ↓
        [PPO训练器]
        无GUI模式运行，仅保存数据
                    ↓
        输出目录结构:
        OUT_DIR/
        ├── models/          # 训练好的神经网络权重
        ├── metadata/        # Unimal元数据（性能指标）
        ├── xml/             # 生成的XML morphology文件
        ├── unimal_init/     # Unimal初始化参数
        ├── rewards/         # 训练过程中的奖励曲线
        ├── videos/          # 可选的视频录制
        └── error_metadata/  # 失败的尝试记录
```

### **2️⃣ 训练代码路径（无可视化）**

```python
# tools/evolution.py
evolve()
  ├─ create_init_unimals()  # 创建初始种群
  └─ launch_subproc()       # 启动子进程
                              ↓
# tools/evo_single_proc.py
ppo_train()
  ├─ make_vec_envs(render_policy=False)  # ❌ 默认不渲染
  ├─ PPO.train()
  │   └─ self.envs.step()                # 仅计算，不显示
  ├─ save_model()                        # 保存训练权重
  ├─ save_rewards()                      # 保存奖励数据
  └─ save_video() (如果enabled)         # 可选：保存视频
```

---

## 🎮 如何启用可视化？

### **方式1️⃣：修改配置文件（推荐）**

在 `configs/evo/lunar_jump.yml` 中添加：
```yaml
RENDER: true              # 启用实时渲染（会降低训练速度）
SAVE_VIDEO: true          # 保存为视频文件
VIDEO_SAVE_FREQ: 100      # 每100代保存一次视频
```

### **方式2️⃣：命令行覆盖参数**
```bash
python tools/evolution.py \
  --cfg configs/evo/lunar_jump.yml \
  EVO.RENDER true \
  EVO.SAVE_VIDEO true
```

### **方式3️⃣：使用可视化评估脚本**

创建一个独立的评估脚本来可视化训练好的模型：

```python
# evaluate_lunar_jump.py
from derl.algos.ppo.envs import make_vec_envs, get_render_func
from derl.config import cfg
import torch

# 加载训练好的模型
xml_file = "OUT_DIR/xml/best_unimal.xml"
model_path = "OUT_DIR/models/best_model.pt"

# 启用渲染
envs = make_vec_envs(
    xml_file=xml_file,
    render_policy=True,  # ✅ 启用可视化
    save_video=False
)

# 加载模型权重
checkpoint = torch.load(model_path)
# ... 加载策略 ...

# 运行可视化评估
render_func = get_render_func(envs)
for ep in range(10):
    obs = envs.reset()
    done = False
    while not done:
        action = policy.act(obs)
        obs, reward, done, info = envs.step(action)
        render_func()  # 显示MuJoCo界面
```

---

## 📈 默认训练行为

### **保存的内容**
- ✅ **神经网络权重** (models/)
- ✅ **奖励曲线数据** (rewards/) - CSV格式
- ✅ **XML形态文件** (xml/)
- ✅ **元数据** (metadata/) - JSON格式
- ❌ **视频** - 默认不保存（除非配置SAVE_VIDEO=true）

### **训练信息输出**
虽然没有GUI，但会在终端输出：
```
Iteration 0, FPS: 1024
  Episode Reward: 25.3 ± 5.2
  Jump Height: 0.45m
  Energy Cost: 2.3

Iteration 1, FPS: 1156
  Episode Reward: 31.2 ± 4.8
  Jump Height: 0.52m
  Energy Cost: 2.1
  ... (持续更新)
```

---

## 💡 建议的工作流程

### **1. 快速测试（无可视化）**
```bash
# 背景训练，集中计算资源
python tools/evolution.py --cfg configs/evo/lunar_jump.yml
```
✅ 优点：快速、高效、适合长期训练
❌ 缺点：无法实时观察机器人行为

### **2. 调试和开发（有可视化）**
```bash
# 修改config启用渲染
vi configs/evo/lunar_jump_debug.yml
# 添加: RENDER: true, EVO.NUM_PROCESSES: 1

python tools/evolution.py --cfg configs/evo/lunar_jump_debug.yml
```
✅ 优点：实时观察机器人行为
❌ 缺点：速度慢（1-2 FPS vs 1000+ FPS）

### **3. 评估已训练模型（有可视化）**
```bash
# 运行上面的 evaluate_lunar_jump.py 脚本
python evaluate_lunar_jump.py
```
✅ 优点：快速查看最优模型的表现

---

## 🔧 配置对比

| 配置选项 | 默认值 | 说明 |
|---------|-------|------|
| `RENDER` | `false` | 是否显示MuJoCo窗口 |
| `SAVE_VIDEO` | `false` | 是否保存视频文件 |
| `NUM_ENVS` | `16` | 并行环境数（影响训练速度）|
| `NUM_PROCESSES` | `4` | 进化的并行进程数 |
| `MAX_ITERS` | `2000` | 每个Unimal的训练迭代数 |

---

## 📊 输出示例

运行后会生成以下结构：
```
OUT_DIR/
├── config.yaml              # 本次训练的配置
├── models/
│   ├── unimal_0.pt         # 第1个Unimal的权重
│   ├── unimal_1.pt
│   └── ...
├── metadata/
│   ├── unimal_0.json       # 性能指标: 奖励、高度等
│   └── ...
├── rewards/
│   ├── unimal_0.csv        # 训练曲线
│   └── ...
├── xml/
│   ├── unimal_0.xml        # 形态定义
│   └── ...
└── videos/                  # 可选视频
    ├── unimal_0.mp4
    └── ...
```

---

## ⚡ 性能对比

| 模式 | FPS | GPU使用率 | 用途 |
|------|-----|---------|------|
| 无渲染（16并行） | **1000+** | 100% | 快速训练 |
| 有渲染（1并行） | **2-5** | 50% | 调试开发 |
| 视频录制 | **10-30** | 80% | 可视化结果 |

---

## 📝 月面跳跃的特殊配置

在 `configs/evo/lunar_jump.yml` 中已配置：
```yaml
GRAVITY: 1.62              # 月球重力加速度
JUMP_REWARD_WEIGHT: 10.0   # 跳跃高度权重（很重要！）
FORWARD_REWARD_WEIGHT: 1.0 # 前进距离权重
ENERGY_COST_WEIGHT: 0.001  # 能量消耗惩罚
TASK: "lunar_jump"         # 任务类型
```

---

## 🎯 总结

| 需求 | 命令 | 特点 |
|------|------|------|
| **快速训练** | `python tools/evolution.py --cfg configs/evo/lunar_jump.yml` | ✅ 无GUI，高效 |
| **查看过程** | 添加RENDER=true | ⚠️ 慢10倍，用于调试 |
| **查看结果** | 写评估脚本 | ✅ 灵活，可保存视频 |

**建议**：默认使用第一种模式进行长期训练，在需要调试时切换到可视化模式。

