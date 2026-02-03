# MVP 阶段（最小可行产品）

> 目标：用 1 个简单的 URDF 构型，在 Isaac Lab 里跑通 LunarJump 任务，并验证 PPO 训练能收敛。

---

## 什么是 MVP？

**最小可行产品 (Minimum Viable Product)**：用最少代码验证核心思路可行。

你这里的 MVP 意思是：
- ✅ **不需要** 4000 个构型 / 完整进化算法
- ✅ 只用 **1 个固定的简单构型**（先手工创建或从现有 xml 转换）
- ✅ 让它在 Isaac Lab 里能：
  1. 加载且不崩溃
  2. 跑 lunar_jump 任务
  3. 计算 jump_height / forward_reward
  4. 用 PPO 训练 30–60 分钟，看到 reward 上升

**为什么先做 MVP？**
- 快速发现"Isaac Lab 是否真的能 work"
- 不用等 3 周才知道整个方向失败
- 一旦 MVP 跑通，剩下的是工程问题，不是原理问题

---

## MVP 检查清单

在你开始做之前，先确认有这些东西：

- [ ] Isaac Lab 已安装（`pip install isaac-lab`）
- [ ] CUDA 环境可用（检查 `nvidia-smi`）
- [ ] PyTorch GPU 版本可用（`torch.cuda.is_available()`）
- [ ] 准备 1 个简单 URDF 文件（可以手工写，也可以从现有 MuJoCo xml 转换）

---

## MVP 阶段的文件清单

你现在这个 `isaac_lab_port/` 目录会有：

```
isaac_lab_port/
├── MVP_README.md（你现在读的这个文件）
├── INTERFACE_CONTRACT.md（数据格式契约）
├── envs/
│   ├── __init__.py
│   ├── isaac_lunar_jump.py（Isaac Lab LunarJump 环境）
│   └── base_env.py（抽象基类，后续继承）
├── assets/
│   ├── simple_robot.urdf（MVP 用的简单测试机器人）
│   └── README.md（资产说明）
└── trainer/
    ├── __init__.py
    └── ppo_trainer_stub.py（PPO 训练入口 stub）
```

---

## MVP 的执行流程

```
1. 准备资产
   └─ isaac_lab_port/assets/simple_robot.urdf
      （一个简单的 4 肢机器人，能站立、能跳）

2. 实现环境
   └─ isaac_lab_port/envs/isaac_lunar_jump.py
      └─ reset() / step(action) / compute_obs() / compute_reward()

3. 实现训练器
   └─ isaac_lab_port/trainer/ppo_trainer_stub.py
      └─ 读取环境，跑 PPO，输出 reward 曲线

4. 执行 MVP 脚本
   └─ python run_mvp_lunar_jump.py
      └─ 30 分钟内看到 reward 上升
```

---

## 下一步（你需要做什么）

### Step 1：准备 URDF（3 种选择）

**选项 A（最快）**：用现有 MuJoCo xml 转换
- 从 `output/lunar_jump/xml/` 里找一个构型
- 用转换脚本转成 URDF（我可以帮写转换脚本）

**选项 B（次快）**：手工写一个简单 URDF
- 参考 `isaac_lab_port/assets/simple_robot.urdf` 的模板
- 改参数即可

**选项 C（最稳妥）**：从 Isaac Lab 官方示例 robot 开始
- 先改官方的 quadruped robot
- 修改成满足 lunar_jump 需求的构型

> 建议先用**选项 B**（手工简单 URDF），最快验证流程。

### Step 2：确认环境实现

我会在 `isaac_lab_port/envs/isaac_lunar_jump.py` 里给出：
- 如何加载 URDF → Isaac Scene
- 如何定义 observation（qpos/qvel/imu）
- 如何计算 reward（forward + jump）
- 如何检测终止条件（跌倒、超高度等）

### Step 3：跑通训练

用 Isaac Lab 的 PPO trainer（或轻量级的参考实现）训练 30 分钟。

---

## 成功的标志（MVP 验收）

当你看到这样的日志，就说明 MVP 成功了：

```
[Isaac Lab] Env reset successful
[Isaac Lab] Episode 1: reward = 0.45, jump_height = 0.12
[Isaac Lab] Episode 10: reward = 1.23, jump_height = 0.25
[Isaac Lab] Episode 50: reward = 3.45, jump_height = 0.58
...
[PPO] Training converged, final return = 45.6
```

（这里数字只是示意，实际数值取决于你的 reward scaling。）

---

## 常见坑（提前避免）

1. **URDF 语法错误**
   - 用 `urdf-parser-py` 或在线验证器检查
   
2. **Isaac 场景加载失败**
   - 确认 URDF 路径正确（绝对路径 or 相对路径）
   - 确认 URDF 中的 inertial/mass 合理（不要太轻）

3. **observation 维度不匹配**
   - 环境返回的 obs shape 要和 PPO 期望的一致
   - 建议先打印 obs shape，确认后再接训练

4. **reward scale 导致训练不动**
   - reward 太小（如 0.001 / step）→ 加大权重
   - reward 太大（如 100 / step）→ 减小权重
   - 一般来说 reward 应该在 [-1, 10] 范围内比较好调

---

## 我下一步给你的代码

我会创建这几个文件：

1. **`INTERFACE_CONTRACT.md`**
   - 明确 genotype → asset → env → fitness 的数据形状
   - 方便后续阶段 B/C 无缝接上

2. **`envs/isaac_lunar_jump.py`**
   - 完整的 Isaac Lab LunarJump 环境实现
   - 可以复制粘贴就用

3. **`assets/simple_robot.urdf`**
   - 一个手工简化的 4 肢机器人
   - 参数可调

4. **`trainer/ppo_trainer_stub.py`**
   - PPO 训练的最小框架
   - 可以用 Isaac 官方 RL pipeline 或轻量级实现

5. **`run_mvp_lunar_jump.py`**
   - MVP 的主入口脚本
   - 一条命令运起来

---

## 时间预期

- 准备 URDF（如果选择手工）：1 小时
- 环境实现（我给代码）：0（你直接用）
- 训练运行 + 调参：2–4 小时
- **总计：半天 ~ 1 天**

如果你装好 Isaac Lab 后有任何报错，截图给我，我可以逐个帮你排查。
