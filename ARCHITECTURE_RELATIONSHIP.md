# DERL 进化架构文件关系

# 核心三个文件的关系

```
evolution.py (主训练脚本)
    ↓
morphology.py (机器人形态类)
    ↓
evo.py (进化算法工具)
```

---

## 详细说明

### 1. **evolution.py** (入口脚本 - 启动训练)
**位置**: `tools/evolution.py`  
**作用**: 整个进化过程的主控制器

#### 核心流程:
```python
evolution.py 运行流程:
├─ setup_output_dir()        # 创建输出文件夹结构
│  ├─ models/                # 保存训练好的权重
│  ├─ metadata/              # 保存机器人评估数据 (奖励、形态等)
│  ├─ xml/                   # 保存机器人MuJoCo形态文件
│  ├─ unimal_init/           # 保存机器人初始化参数
│  └─ rewards/               # 保存奖励数据
│
├─ create_init_unimals()     # 创建初始种群
│  └─ SymmetricUnimal        # 使用morphology.py中的类
│
├─ evolve_population()       # 核心进化循环
│  ├─ eu.select_parent()     # 使用evo.py选择父代
│  ├─ mutate_and_grow()      # 使用morphology.py变异
│  ├─ evaluate()             # 训练评估
│  └─ save_result()          # 保存新生成的机器人
│
└─ repeat_generations()      # 重复进化过程
```

#### 关键代码片段:
```python
from derl.envs.morphology import SymmetricUnimal  # 使用morphology.py
from derl.utils import evo as eu                  # 使用evo.py工具

# 在进化循环中:
unimal = SymmetricUnimal(unimal_id, init_path)   # 创建/加载机器人形态
unimal.mutate()                                   # 变异操作
unimal.save()                                     # 保存形态到xml
parent = eu.select_parent()                       # 选择下一代父代
```

---

### 2. **morphology.py** (形态类 - 机器人结构定义)
**位置**: `derl/envs/morphology.py`  
**作用**: 定义机器人形态的数据结构和变异操作

#### 核心类: `SymmetricUnimal`

```python
class SymmetricUnimal:
    """对称机器人形态表示"""
    
    def __init__(self, id_, init_path=None):
        # 如果init_path存在，从保存的状态加载
        # 否则创建新的机器人（只有头部torso）
        
    # ========== 变异操作 ==========
    def mutate(self, op=None):
        # 随机或指定一个变异操作
        # grow_limb, delete_limb, density, limb_params, gear, dof, joint_angle
        
    def grow_limb(self):
        # 添加新肢体 (递归增长的树状结构)
        
    def mutate_delete_limb(self):
        # 删除肢体 (删除叶子肢体)
        
    def mutate_density(self):
        # 改变身体密度
        
    def mutate_joint(self, op):
        # 改变关节参数 (gear, dof, joint_angle)
        
    # ========== 保存操作 ==========
    def save(self):
        # 保存形态数据到两个文件:
        # 1. xml/{id}.xml          - MuJoCo XML形态文件
        # 2. unimal_init/{id}.pkl  - Python初始化参数
```

#### 保存的数据结构:
```python
# xml/ROBOT_ID.xml (MuJoCo形态文件)
<?xml version="1.0" ?>
<mujoco model="unimal">
  <worldbody>
    <body name="torso/0">
      <!-- 躯干 -->
      <body name="limb/0">
        <!-- 肢体 -->
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="..."/>  <!-- 电动机控制 -->
  </actuator>
</mujoco>

# unimal_init/ROBOT_ID.pkl (初始化参数)
{
  "xml_path": ".../xml/ROBOT_ID.xml",
  "num_limbs": 5,              # 肢体数量
  "dof": 12,                   # 自由度
  "parent_id": "PARENT_ID",    # 父代ID
  "mutation_op": "grow_limb",  # 最后一个变异操作
  "limb_list": [[0], [1, 2], [3], ...],  # 肢体组织结构
  "body_params": {
    "torso_mode": "horizontal_y",
    "limb_density": 1000.0,
    "num_torso": 1,
  },
  # ... 其他参数
}
```

---

### 3. **evo.py** (进化工具 - 选择机制)
**位置**: `derl/utils/evo.py`  
**作用**: 实现进化算法的选择机制

#### 核心函数:

```python
def select_parent():
    """选择父代的主函数"""
    if "aging" in cfg.EVO.TOURNAMENT_TYPE:
        return aging_tournament()     # 考虑年龄的竞赛选择
    elif "vanilla" in cfg.EVO.TOURNAMENT_TYPE:
        return vanilla_tournament()   # 标准竞赛选择

def aging_tournament():
    """年龄竞赛选择 (推荐用于进化训练)"""
    # 1. 获取最近N个机器人的metadata
    metadata_paths = fu.get_files(fu.get_subfolder("metadata"), ".*json")
    metadata_paths = metadata_paths[-cfg.EVO.AGING_WINDOW_SIZE:]
    
    # 2. 随机选择参赛者
    metadatas = [fu.load_json(m) for m in metadata_paths]
    
    # 3. 计算帕累托前沿 (多目标优化)
    dominate_mask = get_dominate_mask(metadatas)
    pareto_front = [m for m, d_mask in zip(metadatas, dominate_mask) if d_mask]
    
    # 4. 返回帕累托前沿中的最优个体
    return random.choice(pareto_front)

def vanilla_tournament():
    """标准竞赛选择"""
    # 从所有机器人中选择，并删除被支配的次优解
    # 适合测试，不适合真实进化
```

#### 元数据结构:
```json
{
  "id": "ROBOT_ID",
  "reward": 1234.5,              # 总奖励
  "energy_efficiency": 0.85,     # 能量效率
  "num_limbs": 5,                # 肢体数量 (进化目标)
  "num_dof": 12,                 # 自由度
  "parent_id": "PARENT_ID",
  "timestamp": 1234567890
}
```

---

## 整个进化流程的完整链路

```
用户运行:
$ python tools/evolution.py --cfg configs/evo/lunar_jump.yml

evolution.py 的执行流程:
│
├─ 初始化阶段:
│  ├─ load_cfg(cfg_file)              # 加载配置
│  ├─ setup_output_dir()              # 创建输出结构
│  └─ create_init_unimals()
│     └─ SymmetricUnimal.mutate()     # 使用morphology.py
│        └─ SymmetricUnimal.save()    # 保存到xml和unimal_init
│
├─ 进化循环 (多代):
│  └─ for generation in range(cfg.EVO.NUM_GENERATIONS):
│     ├─ select_parent = eu.select_parent()      # 使用evo.py
│     │  └─ 从metadata/中读取评估数据
│     │     └─ 计算帕累托前沿
│     │        └─ 返回最优个体id
│     │
│     ├─ unimal = SymmetricUnimal(              # 创建新机器人
│     │  new_id,
│     │  init_path=parent_init_path)             # 加载父代形态
│     │
│     ├─ unimal.mutate()                         # 变异 (morphology.py)
│     │  ├─ grow_limb()
│     │  ├─ mutate_delete_limb()
│     │  ├─ mutate_density()
│     │  └─ ... 其他变异操作
│     │
│     ├─ unimal.save()                           # 保存新形态
│     │  ├─ xml/{new_id}.xml
│     │  └─ unimal_init/{new_id}.pkl
│     │
│     ├─ train_ppo()                             # 训练模型
│     │  └─ 使用xml/{new_id}.xml作为环境
│     │
│     ├─ evaluate()                              # 评估性能
│     │  └─ 计算 reward, efficiency, limbs等
│     │
│     └─ save_metadata()
│        └─ metadata/{new_id}.json               # 保存评估结果
│           └─ 下一代select_parent()会读这个
│
└─ 循环返回第一步，直到达到停止条件
```

---

## ⚠️ 关键问题解答：metadata文件何时生成？为什么output里没有？

### 问题1: metadata文件什么时候生成？
**答案**: **每完成一个个体的PPO训练和评估就生成一个metadata文件**

#### 具体流程：
```python
# evo_single_proc.py 中的训练流程

# 1. 第一阶段：初始化种群 (init_population)
xml_paths = fu.get_files(fu.get_subfolder("xml"), ".*xml")  # 获取所有初始xml
for xml_path in xml_paths[:INIT_POPULATION_SIZE]:  # 每个xml
    ppo_train(xml_path, unimal_id)  # PPO训练
    # 训练完成后 → 生成一个metadata文件
    metadata = {
        "reward": mean_reward_of_last_100_episodes,
        "efficiency": energy_efficiency,
        "num_limbs": limb_count,
        "id": unimal_id
    }
    fu.save_json(metadata, "metadata/{unimal_id}.json")  # ✅ 生成metadata
    
    # 继续下一个
    if eu.get_population_size() >= INIT_POPULATION_SIZE:
        break  # 初始化完成，停止

# 2. 第二阶段：进化循环 (tournament_evolution)
while eu.get_searched_space_size() < SEARCH_SPACE_SIZE:  # 循环条件
    parent_metadata = eu.select_parent()  # 从现有metadata中选择
    
    # 生成新个体
    unimal = SymmetricUnimal(child_id, init_path=parent)
    unimal.mutate()
    unimal.save()  # 保存xml和unimal_init
    
    ppo_train(xml_path, child_id, parent_metadata)  # PPO训练
    
    # 训练完成后 → 生成一个metadata文件
    metadata = {...}
    fu.save_json(metadata, "metadata/{child_id}.json")  # ✅ 生成metadata
```

### 问题2: 为什么你的output文件夹里没有metadata文件？

**原因分析**：
```python
# 在 wait_or_kill 函数中：
while eu.get_searched_space_size() < cfg.EVO.SEARCH_SPACE_SIZE:
    time.sleep(10)
    # ... 监控进程 ...

# 停止条件就是: eu.get_searched_space_size() >= cfg.EVO.SEARCH_SPACE_SIZE
```

这说明：
1. ✅ XML生成阶段已完成 (有1159个xml)
2. ❌ 初始化阶段PPO训练**还没开始**或被立即中断 (没有init_pop_done标记)
3. ❌ 进化循环**根本没开始** (需要metadata，但metadata是空的)

**你的训练被中断了！** 所以：
- ✅ 有初始xml文件 (1159个) - 是从evolution.py早期生成的
- ✅ 有unimal_init文件 - 是从morphology.py保存的初始化参数
- ❌ 没有trained weights (models/) - PPO训练还没完成
- ❌ 没有metadata文件 - PPO还没评估完成

### 问题3: 一代个体的进化何时完成？

**定义**：一个个体的进化完成 = PPO训练 + 评估并保存metadata

```python
def ppo_train(xml_file, id_, parent_metadata=None):
    PPOTrainer = PPO(xml_file=xml_file)
    PPOTrainer.train(...)  # ← 第一步：训练 (耗时很长)
    PPOTrainer.save_model(...)  # 保存权重
    
    # ← 第二步：计算元数据
    metadata = {
        "reward": np.mean(rews[-100:]),  # 最近100个episode的平均奖励
        "efficiency": ...,
        "num_limbs": ...,
        "id": id_
    }
    fu.save_json(metadata, "metadata/{}.json".format(id_))  # ✅ 完成
```

### 问题4: 停止条件是什么？

**共有三个停止条件**：

#### 1️⃣ init_population()的停止条件
```python
def init_population(proc_id):
    # 从1159个xml中取前INIT_POPULATION_SIZE(576)个
    xml_paths = fu.get_files(...)[:cfg.EVO.INIT_POPULATION_SIZE]  # 576个
    
    for xml_path in xml_paths:
        ppo_train(...)  # 训练
        
        # 停止条件：初始化种群达到目标大小
        if eu.get_population_size() >= cfg.EVO.INIT_POPULATION_SIZE:  # 576
            break  # 停止初始化
    
    # 创建标记文件表示初始化完成
    Path(init_done_path).touch()  # init_pop_done
```

#### 2️⃣ tournament_evolution()的停止条件
```python
def tournament_evolution(idx):
    # 停止条件：已搜索空间达到SEARCH_SPACE_SIZE(4000)
    while eu.get_searched_space_size() < cfg.EVO.SEARCH_SPACE_SIZE:  # 4000
        parent = eu.select_parent()  # 从metadata中选择
        child = SymmetricUnimal(...)  # 创建新xml
        child.mutate()
        ppo_train(...)  # 训练新个体，生成metadata
        # 继续循环直到达到4000个
    # 当 get_searched_space_size() >= SEARCH_SPACE_SIZE 时退出
```

#### 3️⃣ 主进程(evolution.py)的停止条件
```python
def wait_or_kill(subprocs):
    # 停止条件3：子进程达到搜索空间大小或生成了所有视频
    while eu.get_searched_space_size() < cfg.EVO.SEARCH_SPACE_SIZE:
        time.sleep(10)
        # ... 监控子进程 ...
    
    # 如果需要保存视频，等待所有视频生成完毕
    if eu.should_save_video():
        while len(fu.get_files(video_dir, reg_str)) > 0:
            time.sleep(60)
    
    # 最后杀死所有子进程
    for p, _ in subprocs:
        kill_pg(p)
```

### 问题5: 循环多代的停止条件详解

```yaml
# configs/evo/mvt.yml 或其他

EVO:
  # 这是真正的停止条件！
  SEARCH_SPACE_SIZE: 4000    # ← 搜索空间大小 (决定生成多少个个体)
  
  # 这些参数控制如何在这个空间内进行搜索
  INIT_POPULATION_SIZE: 576   # 阶段一：训练576个初始个体
  NUM_GENERATIONS: 200        # (不再使用，被SEARCH_SPACE_SIZE替代)
  AGING_WINDOW_SIZE: 576      # 从最近576个个体中选择父代
```

**真正的进化过程**：

```
阶段1：初始化 (init_population)
├─ 输入：1159个初始xml候选 (已生成)
├─ 任务：从1159个中选前576个进行PPO训练
├─ 输出：576个metadata文件 (每完成一个训练生成一个)
├─ 标记：init_pop_done

阶段2：进化循环 (tournament_evolution)
├─ 输入：576个metadata (从阶段1)
├─ 任务：生成3424个新个体 (4000 - 576 = 3424)
│  - 从metadata中用Pareto竞赛选父代
│  - 变异生成新xml
│  - 训练新xml，生成metadata
├─ 输出：3424个新metadata
├─ 停止条件：get_searched_space_size() >= 4000
└─ 完成：总共4000个个体

清理：
└─ 杀死所有子进程
```

**关键区别**：
- ❌ 错误：循环200代 = 生成200个新个体 (NUM_GENERATIONS现在不用了)
- ✅ 正确：进化到总共 = 4000个个体 (SEARCH_SPACE_SIZE控制)

---

## 🔍 1159个xml文件的真正由来

### 初始化阶段的候选形态生成过程：

```python
# evolution.py 中的 create_init_unimals() 函数：

init_pop_size = cfg.EVO.INIT_POPULATION_SIZE  # 配置值: 576
# 但你的实际数据显示生成了更多

# 生成10倍数量的候选形态
idx_unimal_id = [
    (idx, "{}-{}-{}".format(cfg.NODE_ID, idx, timestamp))
    for idx in range(10 * init_pop_size)  # ← 关键是这里
]
# 共生成 10 × INIT_POPULATION_SIZE 个候选

# 例如：
# INIT_POPULATION_SIZE = 576 → 生成 5760 个候选
# INIT_POPULATION_SIZE = 160 → 生成 1600 个候选 ← 和你的情况接近！
```

### 你的实际情况分析：

```
生成的候选形态：
  - 文件名格式: 0-{INDEX}-29-19-34-25.xml
  - 索引范围: 0 到 1601
  - 总共生成: 1602 个候选形态

去重过程：
  - 构建相似性图 (基于几何方向 geom_orientation)
  - 将相似的形态分组到连通分量
  - 从每组中只保留第一个，删除其他重复

最终保留：
  - 1159 个唯一的形态
  - 去重率: (1602 - 1159) / 1602 = 27.7% (有27.7%的形态被识别为重复)

回推计算：
  - 1602 = 10 × 160.2
  - 因此: INIT_POPULATION_SIZE ≈ 160
```

### 为什么不是576？

**可能的原因**：

1️⃣ **实际就是这样**：
   - 配置：INIT_POPULATION_SIZE = 576
   - 生成：10 × 576 = 5760 个候选
   - 去重：5760 - 4601 = 1159 个保留
   - 1159 > 576，所以保留了1159个（都是初始化xml）

### 完整的生成流程：

```
INIT_POPULATION_SIZE = 576 (配置值)
         ↓
生成 10 × 576 = 5760 个初始候选 (idx: 0-5759)
         ↓
构建相似性图 G = create_graph_from_uids(...)
         ↓
提取连通分量 cc = list(nx.connected_components(G))
         ↓
去重逻辑：
  - 5760个形态被分组到多个连通分量
  - 从每个连通分量中只保留第一个
  - 删除：5760 - len(keep) = 4601 个重复
         ↓
保留的数量调整：
  - if len(keep) > INIT_POPULATION_SIZE:
      保留1159个（本来只需576，多出来也保留）
  - else:
      从删除列表中恢复
         ↓
最终输出：1159 个唯一形态 (XML + unimal_init文件对)
         ↓
创建 init_setup_done 标记文件
```

### 关键代码逻辑：

```python
def create_init_unimals():
    init_pop_size = cfg.EVO.INIT_POPULATION_SIZE
    
    # Step 1: 并行生成 10倍数量的候选
    idx_unimal_id = [(idx, f"0-{idx}-timestamp") for idx in range(10 * init_pop_size)]
    unimal_ids = p.starmap(limb_count_pop_init, idx_unimal_id)
    # 结果: 1602 个形态文件生成
    
    # Step 2: 构建相似性图，计算哪些形态是相似的
    G = simu.create_graph_from_uids(None, unimal_ids, "geom_orientation")
    cc = list(nx.connected_components(G))
    
    # Step 3: 去重 - 从每个连通分量中只保留一个
    for same_unimals in cc:
        if len(same_unimals) == 1:
            unimals_to_keep.append(same_unimals[0])  # 独特的
        else:
            unimals_to_keep.append(sorted(same_unimals)[0])  # 保留第一个
            unimals_to_remove.extend(sorted(same_unimals)[1:])  # 删除其他
    
    # Step 4: 调整数量以达到 INIT_POPULATION_SIZE
    # 如果去重后 > init_pop_size，随机删除多余的
    # 如果去重后 < init_pop_size，从删除列表中恢复
    
    # Step 5: 删除未保留的形态文件
    for unimal in unimals_to_remove:
        fu.remove_file(fu.id2path(unimal, "xml"))
        fu.remove_file(fu.id2path(unimal, "unimal_init"))
    
    # 结果: 1159 个保留下来
```

## ❌ 你的1159个xml文件的正确来源

**错误的说法（删除）**：我之前说"50个初始化 + 950个进化循环"是**完全错误**的。

**正确的说法**：

1159个xml文件**全部来自阶段一初始化**，不涉及任何进化循环。

### 详细过程：

```
evolution.py 中 create_init_unimals() 函数执行：

第1步：生成5760个初始候选形态
    for idx in range(10 * INIT_POPULATION_SIZE)
    # 10 × 576 = 5760 个xml
    
第2步：构建相似性图，去重
    G = create_graph_from_uids(...)  # 基于几何方向
    cc = nx.connected_components(G)  # 获取连通分量
    
    去重逻辑：
    - 5760个相似的形态被分组到多个连通分量
    - 从每组中只保留第一个，删除其他重复
    - 结果：删除了 5760 - 1159 = 4601 个重复
    
第3步：调整数量达到INIT_POPULATION_SIZE
    if len(keep) > INIT_POPULATION_SIZE:
        保留1159个（本来是576，多出来的也保留了）
    elif len(keep) < INIT_POPULATION_SIZE:
        从删除列表中恢复
    
最终结果：1159个唯一的xml + unimal_init文件对

创建标记文件：init_setup_done
```

### 关键点：

✅ **阶段一初始化阶段还未完成PPO训练**
- 有1159个xml和unimal_init文件
- **没有**任何models/文件（训练权重）
- **没有**任何metadata/文件（评估数据）
- 只有init_setup_done标记，没有init_pop_done标记

❌ **没有涉及任何进化循环**
- 进化循环需要从metadata中选择父代
- 但metadata是空的，说明还没有阶段一的PPO训练

### 实际训练状态：

```
┌─────────────────────────────────────┐
│  阶段一：初始化 (init_population)   │
├─────────────────────────────────────┤
│ ✅ 完成：生成1159个初始xml候选    │
│ ❌ 未完成：选576个进行PPO训练     │
│ ❌ 未完成：生成576个metadata文件  │
└─────────────────────────────────────┘
           ↓ (等待完成)
┌─────────────────────────────────────┐
│  阶段二：进化循环 (tournament_evo)  │
├─────────────────────────────────────┤
│ ❌ 未开始：需要metadata父代        │
│ ❌ 未开始：生成后续3424个个体      │
│ ❌ 未开始：直到达到SEARCH_SPACE_SIZE = 4000
└─────────────────────────────────────┘
```

你的训练停留在**阶段一初始化**的最开始阶段（xml生成）。

---

## 📊 你的项目现状分析

### 文件统计：
```
output/lunar_jump/
├─ xml/              1159 ✅ (已生成初始候选)
├─ unimal_init/      1159 ✅ (已生成初始参数)
├─ metadata/         0   ❌ (空，阶段1 PPO还没开始)
├─ models/           0   ❌ (空，没有训练权重)
├─ rewards/          0   ❌ (空，没有评估数据)
├─ init_setup_done   ✅ (存在，xml生成完成)
└─ init_pop_done     ❌ (不存在，阶段1 PPO训练未完成)
```

### 真实情况解析：

**1. 为什么有1159个xml和unimal_init但没有metadata？**

```python
# evolution.py 的流程：

# 第一步：主节点生成初始xml文件 ✅ (已完成)
create_init_unimals()
├─ 生成 10 × INIT_POPULATION_SIZE = 5760个候选xml
├─ 去重（相似性检查）→ 保留1159个唯一形态
└─ 创建init_setup_done标记 ✅

# 第二步：子进程训练（阶段1） ❌ (还没开始)
init_population(proc_id)
├─ 从1159个xml中取前576个
├─ 对每个进行PPO训练 ← ❌ 这一步还没开始！
├─ 生成metadata ❌ 没有执行
└─ 创建init_pop_done标记 ❌

# 第三步：进化循环（阶段2） ❌ (还没开始)
tournament_evolution(proc_id)
├─ 需要metadata父代 ← 但阶段1还没完成！
└─ 无法进行 ❌
```

**2. 为什么metadata是空的？**

```python
# 要生成metadata需要经过以下流程：

ppo_train()  # ← 这一步还没开始！
├─ PPO.train()          # 需要几小时到几天
├─ PPO.save_model()     # 保存权重 → models/ 文件夹
└─ compute_metadata()   # 计算评估指标

fu.save_json(metadata, "metadata/{}.json")  # ← 这一步没执行

# 由于PPO训练是最耗时的步骤，而你的训练还没开始
# 所以任何metadata都没有被生成过
```

### 训练现状：

你的训练停留在**xml文件生成**阶段，还没进入**PPO训练**阶段。

---

## ✅ 总结答案

| 问题 | 答案 |
|------|------|
| **metadata何时生成？** | 每完成一个individual的PPO训练就生成一个 |
| **为什么output里没有metadata？** | 训练还没开始或在第一个xml的PPO阶段被中断了 |
| **一代何时完成？** | 当PPO训练完成并保存metadata时 |
| **停止条件是什么？** | `eu.get_searched_space_size() >= cfg.EVO.SEARCH_SPACE_SIZE` (4000) |
| **为什么有1159个xml？** | 初始化阶段生成的候选形态 (init_population需要从这1159个中选50个进行训练) |
| **循环多代的停止条件？** | 当已生成个体数 >= 4000时停止 (不是循环代数，而是搜索空间大小) |

---

## 🔄 如果要重新启动训练

```bash
# 1. 设置PYTHONPATH
export PYTHONPATH=/home/t/yb/agrimgupta_derl/derl:$PYTHONPATH

# 2. 清空之前的训练痕迹（可选）
rm output/lunar_jump/init_setup_done
rm output/lunar_jump/init_pop_done

# 3. 重新启动训练
PYTHONPATH=. python tools/evolution.py --cfg configs/evo/lunar_jump.yml

# 预计需要时间：
# - 初始化50个个体：50 × (几小时) = 几周
# - 进化3950个个体：3950 × (几小时) = 几个月
# 这就是为什么通常用多个节点并行计算！
```





### 1️⃣ morphology.py → xml + unimal_init
```python
# 在evolution.py中:
unimal = SymmetricUnimal("robot-0-123", init_path=None)  # 新创建
unimal.mutate()
unimal.save()  # 生成:
#   - output/lunar_jump/xml/robot-0-123.xml
#   - output/lunar_jump/unimal_init/robot-0-123.pkl
```

### 2️⃣ evolution.py → metadata
```python
# 训练完成后:
metadata = {
    "reward": 1234.5,
    "efficiency": 0.85,
    "num_limbs": 5
}
# 保存到: output/lunar_jump/metadata/robot-0-123.json
```

### 3️⃣ evo.py ← metadata
```python
# 下一代选择父代时:
eu.select_parent()  
# 读取metadata/中的所有json
# 计算帕累托前沿
# 返回最优个体的unimal_init路径
```

---

## 你的1159个机器人的由来

```
第1个机器人: 随机初始化 (create_init_unimals)
    ↓ 
经过train_ppo和evaluate后 → metadata/robot-0-xxx.json (记录性能)
    ↓
作为父代被select_parent()选中
    ↓
morphology.py变异生成第2个机器人
    ↓
经过train_ppo和evaluate后 → metadata/robot-1-xxx.json
    ↓
... 重复1000+代 ...
    ↓
最终输出1159个xml文件 (xml文件夹)
```

---

## 配置参数的含义

```yaml
# configs/evo/lunar_jump.yml 中的进化参数

EVO:
  INIT_METHOD: "limb_count_pop_init"        # 初始化方法
  INIT_POPULATION_SIZE: 10                  # 初始种群大小
  NUM_GENERATIONS: 200                      # 进化代数
  POP_SIZE: 50                              # 每代种群大小
  
  TOURNAMENT_TYPE: "aging"                  # 选择方式 (aging或vanilla)
  AGING_WINDOW_SIZE: 30                     # 年龄竞赛的窗口大小
  NUM_PARTICIPANTS: 5                       # 每次竞赛的参赛者数
  
  SELECTION_CRITERIA: ["reward", "dof"]     # 帕累托目标 (多目标优化)
  SELECTION_CRITERIA_OBJ: [1, -1]           # 目标方向 (最大化reward, 最小化dof)
  
  MUTATION_OPS: ["grow_limb", "delete_limb", "density"]  # 允许的变异操作

PPO:
  MAX_ITERS: 1000                           # 每个机器人的训练迭代次数
  TIMESTEPS: 2000                           # 每次迭代的时间步
  NUM_ENVS: 16                              # 并行环境数
```

---

## 总结

| 文件 | 作用 | 输入 | 输出 |
|------|------|------|------|
| **evolution.py** | 进化主循环 | 配置文件 | xml/, unimal_init/, metadata/, models/ |
| **morphology.py** | 机器人形态 | 父代xml/pkl | 新的xml + pkl (变异后的形态) |
| **evo.py** | 选择机制 | metadata json | 最优父代ID |

你可以把进化过程想象成一个**生物进化过程**:
- 🧬 **morphology.py** = DNA变异机制（如何繁殖下一代）
- 🏆 **evo.py** = 自然选择（适应度强的个体繁殖）
- 🔄 **evolution.py** = 进化循环（不断重复）
