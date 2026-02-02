# DERL → Isaac Lab 完全迁移指南（GPU 仿真 + GPU 训练）

> 目标：把当前基于 **MuJoCo (CPU)** 的 DERL（构型进化 + PPO）完整迁移到 **Isaac Lab (Isaac Sim, GPU)**，让 **仿真 rollout 与 RL 训练端到端在 GPU 上并行**。
>
> 本文档强调：
> - **需要改哪些地方（按文件/模块拆解）**
> - **迁移步骤（分阶段交付，避免半路返工）**
> - **可行性与主要风险**
> - **建议的最小可验证原型（MVP）**

---

## 0. TL;DR（结论 + 预期收益）

- ✅ **可行性**：可行。DERL 的“进化逻辑”和“训练/仿真实现”是弱耦合的（通过 xml/metadata 文件连接），非常适合做“后端替换”。
- ✅ **最佳路线**：**不要先改 DERL 做 GPU**（MuJoCo 物理仍在 CPU，收益有限且会形成技术债），而是 **直接迁移到 Isaac Lab**。
- ✅ **改动规模**：改动较大，但集中在 **环境层 + 构型输出格式 + 训练入口** 三块。
- ✅ **核心收益**：用 Isaac Lab 的 GPU 并行环境能力，通常会获得数量级加速（目标区间 30–50×，取决于环境复杂度与并行度）。

---

## 1. 当前 DERL 架构（你要迁移什么）

DERL 当前从代码上可以分成三层：

### 1.1 构型（Morphology / Design Space）

- 入口类：`derl/envs/morphology.py::SymmetricUnimal`
- 作用：在 MuJoCo XML 上做“增删肢体 + 参数突变”，并保持左右对称。
- 输出：
  - `output/<task>/xml/<id>.xml`（MuJoCo 模型定义）
  - `output/<task>/unimal_init/<id>.json`（可复现构型的中间态）

### 1.2 仿真/任务环境（MuJoCo env）

- Gym 注册：`derl/envs/__init__.py` 注册 `Unimal-v0`
- 环境工厂：`derl/envs/tasks/task.py::make_env(xml_path=...)`
- 任务实现：`derl/envs/tasks/*.py`（如 `lunar_jump.py`）
- 基类：`derl/envs/tasks/unimal.py`（MuJoCo 物理仿真部分）

### 1.3 训练 + 进化调度（DERL 方法本体）

- PPO：`derl/algos/ppo/`（当前把网络放 GPU，但环境仍是 CPU MuJoCo）
- 大循环：`tools/evolution.py`
  - master 创建 init 种群 + 启动 18 个子进程
- 子进程：`tools/evo_single_proc.py`
  - `init_population()`：训练初始化种群
  - `tournament_evolution()`：循环：选父代→变异得到子代→训练→写 metadata
- 选择逻辑：`derl/utils/evo.py`
  - aging tournament + Pareto

> 迁移本质：把 **“MuJoCo 环境 + VecEnv + PPO训练方式”** 换成 **“Isaac Lab GPU 环境 + Isaac 训练栈”**；
> 进化算法（选择/变异/终止条件）尽量保留。

---

## 2. Isaac Lab 迁移后的目标架构

迁移后，你希望达到：

- 仿真：Isaac Sim（GPU 物理引擎）
- 采样：单进程（或少量进程）在 GPU 上并行很多环境（num_envs = 256/512/1024…）
- 训练：PPO/Actor-Critic 在 GPU 上训练，观测/奖励/终止都用 torch 张量批处理
- 进化：仍然是“生成构型 → 训练评估 → 写回指标 → tournament/pareto 选择”

一个合理的最终形态是：

1. `genotype`（构型基因）在 Python 中表示（树/图结构）
2. `genotype -> asset`（URDF/USD）转换器
3. Isaac Lab env 读取 asset，运行任务并输出奖励/metric
4. RL trainer 返回该构型的 fitness 指标（如 `__reward__jump` 或 `metric`）
5. Evolution loop 负责选择/变异/记录 lineage

---

## 3. 需要改哪些地方？（按模块列清单）

### 3.1 必须重写：环境层（最大改动）

原因：目前 `UnimalEnv`/`task.py` 强绑定 `mujoco_py` + XML merge。

需要替换/新增：

- 替代 `derl/envs/tasks/unimal.py`：实现 Isaac Lab 环境（torch batch 版）
- 替代 `derl/envs/tasks/task.py`：不再拼 MuJoCo XML，而是构建 Isaac Scene + 载入资产
- 重写各任务：`derl/envs/tasks/*.py`
  - 奖励函数、终止条件、观测提取全部改为 torch 张量批处理

**改动规模**：大（但逻辑多是“照搬符号意义”，例如 lunar_jump 的 jump_height/forward_reward 很清楚）。

### 3.2 中等改动：构型输出（XML → URDF/USD）

`SymmetricUnimal` 的“变异逻辑”可以保留，但底层不再维护 XML 树。

建议做法：

- 抽象出 `Genotype` 数据结构（拓扑 + 参数）
- 保留 `mutate()` 的分支（grow_limb / delete_limb / limb_params / dof / density / gear / joint_angle）
- 实现一个 `genotype_to_urdf()` 或 `genotype_to_usd()`

**改动点**集中在：
- `SymmetricUnimal.save()`：不再落 MuJoCo XML，而是落 URDF/USD
- 现有 `derl/utils/xml.py` 的大量 XML helper 将逐步无用

### 3.3 建议替换：PPO训练栈

原因：现有 PPO 依赖 Gym VecEnv（`SubprocVecEnv`/`VecNormalize`）
而 Isaac Lab 环境是原生 GPU 批处理。

建议方案：

- 选择 Isaac Lab 推荐训练栈（Isaac 官方示例 + PPO）
- Evolution loop 只把每个构型的训练当作一个“子任务调用”，拿到 fitness 即可。

> 换句话说：不要硬搬 `derl/algos/ppo/*`，而是把它当“参考实现”。

### 3.4 中等改动：进化调度

保留：`derl/utils/evo.py`（pareto, aging tournament）

重写/简化：
- `tools/evolution.py` 里的 `launch_subproc / wait_or_kill` 等进程管理
- `tools/evo_single_proc.py::ppo_train()` 改为 Isaac trainer 调用

仍然可以保留：
- metadata 落盘（用于断点续跑，审计 lineage/family ）
但不建议继续用“文件数量”做同步机制。

---

## 4. 分阶段迁移路线（避免一次性大爆炸）

### 阶段 A：最小可验证原型（MVP）（优先做）

目标：证明“Isaac Lab 能加载 1 个构型 + 能跑 LunarJump + 能训练出正向 reward”。

交付物：
- 一个固定构型的 URDF/USD（手工做也行）
- 一个 Isaac Lab 环境（LunarJump）
- 一个 PPO 训练脚本跑通

验收标准：
- env `reset/step` 正常（无 NaN、无爆炸）
- `jump_height` 类似指标能计算
- 训练 30–60 分钟能看到 reward 上升（不要求与 MuJoCo 数值完全一致）

### 阶段 B：接通“构型生成器”（Genotype → Asset）

目标：让 `SymmetricUnimal` 的“变异”能批量产出可加载的资产。

交付物：
- `genotype` 表示 + `mutate()`
- `genotype_to_urdf/usd` 转换器
- 小规模测试：生成 50–100 个构型，逐个加载 Isaac 环境不崩

验收标准：
- 生成的资产可加载率高（>= 95%）
- 对失败构型有 fallback（例如丢弃并重新采样）

### 阶段 C：恢复完整进化循环（tournament + pareto）

目标：把 `tools/evolution.py` 的“进化算法”跑起来，但后端 trainer/physics 都是 Isaac。

交付物：
- 新版 `evolution_isaac.py`（或保留原名，但内部切换）
- 断点续跑（metadata/lineage）
- 统计：当前 Pareto front、最优构型导出、视频/渲染

验收标准：
- 在较小搜索空间（如 200–500）下能跑完
- 能产生比随机搜索更好的构型

---

## 5. 三个关键风险点（以及怎么提前验证）

### 风险 1：MuJoCo 物理参数 ↔ Isaac 物理参数不一致

体现：同样构型在 Isaac 里更滑/更软/更不稳定。

缓解：
- 先选 1 个简单构型做“轨迹对比”
- 优先对齐重力、关节限制、摩擦、密度/惯量

### 风险 2：奖励/观测实现方式变化导致训练不稳定

缓解：
- 从最简单观测开始（proprioception：qpos/qvel/imu）
- 奖励按 DERL 的定义逐步加（先 forward，再 jump，再能量惩罚）

### 风险 3：训练栈切换成本

缓解：
- 不硬搬现有 `derl/algos/ppo`，直接用 Isaac Lab 推荐 PPO
- Evolution loop 只看“最终 fitness”

---

## 6. 工作量预估（偏工程现实）

> 这是在“你熟悉 Python + RL，Isaac Lab 需要学习”的情况下的经验估计。

- 阶段 A（MVP）：3–7 天
- 阶段 B（构型生成器接通）：1–2 周
- 阶段 C（完整进化循环）：1–2 周

总计：约 3–5 周（并行学习情况下）。

---

## 7. 建议的仓库改造方式（不破坏原 DERL）

建议新增一个顶层目录，避免污染现有 MuJoCo 版本：

- `isaac_lab_port/`
  - `envs/`（Isaac Lab envs）
  - `assets/`（生成的 URDF/USD）
  - `trainer/`（PPO 训练封装）
  - `evolution/`（进化循环封装）

最终你可能会维持两个后端：
- `mujoco_backend/`（用于对齐验证、复现实验）
- `isaac_backend/`（主力训练）

---

## 8. 下一步（我建议你现在就做的 2 件事）

1. **定 MVP 目标**：你希望先跑哪个任务？建议从 `lunar_jump` 开始（奖励定义已经很清晰）。
2. **选资产格式**：URDF 优先还是 USD 优先？
   - 如果目标是“尽快跑起来”：URDF
   - 如果目标是“长期性能/可视化/材质完整”：USD

如果你确认“先 URDF + lunar_jump MVP”，我可以下一步帮你：
- 在仓库里创建 `isaac_lab_port/` 的目录结构
- 写一个“接口契约”文档：`genotype -> asset -> env -> fitness` 的 data shape
- 给出最小 stub（不需要你立刻把 Isaac Lab 装好，也能先把代码骨架搭起来）
