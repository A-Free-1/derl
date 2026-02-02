# 🎮 原仓库可视化指令详解

## 📌 原始指令
```bash
python tools/terrain_builder.py --cfg configs/evo/mvt.yml
```

---

## 🎯 这个指令的含义

### **作用：启动交互式MuJoCo环境查看器**

这个命令会：
1. ✅ **加载环境配置** （从 `configs/evo/mvt.yml`）
2. ✅ **创建MuJoCo物理模拟环境**
3. ✅ **弹出可视化窗口**（实时3D渲染）
4. ✅ **启动交互式控制器**（键盘控制机器人）

---

## 📊 MVT（Manipulation-Terrain-Vault）配置说明

`mvt.yml` 配置了一个**操纵任务 (Manipulation) 的可视化环境**：

```yaml
ENV_NAME: 'Unimal-v0'        # Unimal机器人环境
TASK: "manipulation"         # 任务类型：推箱子/物体操纵
MODULES: 
  - "Agent"                  # Unimal机器人
  - "Terrain"                # 地形（曲线/斜坡/台阶）
  - "Objects"                # 物体（待操纵的箱子）

TERRAIN:
  SIZE: [30, 20, 1]          # 地形尺寸：30×20米
  TYPES: 
    - "curve_slope"          # 曲线斜坡
    - "steps"                # 台阶
    - "rugged_square"        # 凹凸平面
  BOUNDARY_WALLS: true       # 边界墙壁

OBJECT:
  BOX_SIDE: 0.20             # 箱子大小：0.2m
  SUCCESS_MARGIN: 0.75       # 成功判定距离
```

---

## 🎮 可视化窗口的交互操作

启动后，会弹出MuJoCo 3D窗口，可进行以下操作：

### **键盘控制**

| 按键 | 功能 | 说明 |
|------|------|------|
| **N** | 下一个种子 | 加载新的环境配置 (seed+1) |
| **P** | 上一个种子 | 加载之前的环境配置 (seed-1) |
| **A** | 减少动作 | 降低当前选中动作的力度 (-0.05) |
| **Z** | 增加动作 | 增加当前选中动作的力度 (+0.05) |
| **J** | 前一个动作 | 切换到前一个关节的控制 |
| **K** | 后一个动作 | 切换到后一个关节的控制 |
| **ESC** | 退出 | 关闭窗口 |

### **鼠标控制**
- **中键拖拽** - 旋转视角
- **右键拖拽** - 平移视角
- **滚轮** - 缩放/放大

### **显示的信息**
窗口会实时显示：
```
┌─────────────────────────────────────┐
│ Camera Name                          │
│ [当前相机名称]                       │
├─────────────────────────────────────┤
│ Reset env; (current seed: 1409)     │
│ N - next / P - previous             │
├─────────────────────────────────────┤
│ Apply action: A (-0.05) / Z (+0.05)│
│ on action index 0 out 9             │
│ J / K                               │
├─────────────────────────────────────┤
│ Reset took: 0.25 sec.              │
│ Action: [0.2, -0.1, 0.0, ...]      │
└─────────────────────────────────────┘
```

---

## 🔄 执行流程

```python
terrain_builder.py
    ↓
parse_args()  # 解析命令行参数 --cfg configs/evo/mvt.yml
    ↓
cfg.merge_from_file()  # 加载配置文件
    ↓
make_env()  # 创建环境
    ├─ Unimal机器人模型
    ├─ 地形（Terrain）
    ├─ 物体（Objects）
    └─ 物理引擎 (MuJoCo)
    ↓
EnvViewer  # 启动交互式查看器
    ├─ MjViewer (MuJoCo 3D渲染)
    ├─ 键盘回调 (key_callback)
    ├─ 鼠标控制
    └─ run() # 主循环
    ↓
while True:
    env.step(action)  # 执行动作
    render()  # 渲染3D场景
    display_overlays()  # 显示信息
```

---

## 📋 不同配置的可视化

### **exploration.yml - 探索任务**
```yaml
TASK: "exploration"
TERRAIN: 50×50 大地形，中心平坦
# 查看机器人在大型地形上的探索行为
```

运行：
```bash
python tools/terrain_builder.py --cfg configs/eval/exploration.yml
```

### **obstacle.yml - 障碍物任务**
```yaml
TASK: "obstacle"
MODULES: ["Agent", "Terrain", "Obstacles"]
# 查看机器人躲避障碍物的能力
```

### **patrol.yml - 巡逻任务**
```yaml
TASK: "patrol"
# 查看机器人在指定路线上的行为
```

---

## 🌍 对比：可视化的三种方式

### **方式1️⃣：terrain_builder.py（推荐用于环境检查）**
```bash
python tools/terrain_builder.py --cfg configs/evo/mvt.yml
```
✅ 优点：
- 交互式控制机器人
- 实时3D可视化
- 便于调试环境配置
- 手动测试不同的种子

❌ 缺点：
- 只能手动控制，不是AI策略
- 不适合评估训练好的模型

### **方式2️⃣：修改evolution.py添加RENDER（用于训练过程可视化）**
```yaml
# configs/evo/lunar_jump_debug.yml
RENDER: true
NUM_PROCESSES: 1  # 只用1个进程便于观察
```
```bash
python tools/evolution.py --cfg configs/evo/lunar_jump_debug.yml
```
✅ 优点：
- 看AI正在训练的过程
- 观察策略的演变

❌ 缺点：
- 速度非常慢
- 难以长期训练

### **方式3️⃣：评估脚本（用于查看训练成果）**
```python
# evaluate.py
env = make_env(xml_file="output/xml/best_unimal.xml")
viewer = EnvViewer(env)
viewer.run()
```
✅ 优点：
- 用训练好的模型运行
- 查看最终效果

❌ 缺点：
- 需要编写脚本

---

## 🚀 对于月面跳跃任务的可视化

### **1️⃣ 查看环境配置**
```bash
# 使用terrain_builder来检查环境设置
python tools/terrain_builder.py --cfg configs/evo/lunar_jump.yml
```

### **2️⃣ 手动探索环境**
在弹出的窗口中：
- 用 **A/Z** 键控制机器人的各个关节
- 用 **N/P** 键切换不同的环境变化
- 观察机器人在低重力下的跳跃行为

### **3️⃣ 查看机器人形态**
```bash
# 在terrain_builder窗口中，可以看到：
# - Unimal的体型和肢体配置
# - 关节活动范围
# - 与地形的交互
# - 跳跃时的物理效果
```

---

## 📊 terrain_builder.py vs evolution.py

| 功能 | terrain_builder.py | evolution.py |
|------|-------------------|------------|
| **用途** | 环境可视化 | 模型训练 |
| **显示内容** | 环境+手动控制 | 环境+AI策略 |
| **交互方式** | 键盘手动 | 自动学习 |
| **实时渲染** | ✅ 强制启用 | ❌ 默认关闭 |
| **速度** | 取决于电脑 | 快速（无GUI）或很慢（有GUI） |
| **用场景** | 调试环境配置 | 训练AI策略 |

---

## 💡 实用建议

### **快速检查环境是否正确**
```bash
python tools/terrain_builder.py --cfg configs/evo/lunar_jump.yml
```
- 检查机器人模型是否加载正确
- 检查地形是否符合预期
- 检查物理参数（重力等）是否生效

### **调试机器人控制**
在窗口中：
1. 用A/Z键调整各个关节的力度
2. 观察机器人如何响应
3. 理解机器人的运动能力

### **对比不同环境**
```bash
# 对比地球和月球的行为差异
python tools/terrain_builder.py --cfg configs/eval/exploration.yml  # 地球重力
python tools/terrain_builder.py --cfg configs/evo/lunar_jump.yml    # 月球重力
```

---

## 🎯 总结

**`python tools/terrain_builder.py --cfg configs/evo/mvt.yml` 的含义：**

> 加载MVT（操纵任务）的环境配置，启动一个**交互式MuJoCo3D查看器**，允许用户通过键盘手动控制机器人，实时观看和调试环境配置。

**关键差异：**
- ❌ **不是**自动训练AI
- ✅ **是**环境可视化和手动探索
- ✅ **用于**调试环境设置、理解任务配置

**对月面跳跃的应用：**
```bash
# 检查月面跳跃环境
python tools/terrain_builder.py --cfg configs/evo/lunar_jump.yml

# 然后开始训练（无GUI）
python tools/evolution.py --cfg configs/evo/lunar_jump.yml
```

