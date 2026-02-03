# 系统硬件检查报告（双系统安装可行性）

> 日期：2026-02-02  
> 用户：t  
> 系统：Ubuntu 20.04.6 LTS  

---

## 📊 硬件配置总览

### ✅ 完全满足条件

| 项目 | 配置 | 要求 | 状态 |
|------|------|------|------|
| **CPU** | Intel Xeon E-2278G (16核) | 任意 | ✅ 超出要求 |
| **RAM** | 15GB | 4GB 最低 | ✅ 充足 |
| **GPU** | RTX 3090 (24GB VRAM) | 无 | ✅ 完美（Isaac Lab 推荐） |
| **驱动** | NVIDIA 535.183.01 | 450+ | ✅ 最新 |
| **CUDA** | 12.2 | 12.0+ | ✅ 支持 |

---

## 💾 磁盘空间分析

### 当前分区情况

```
磁盘: /dev/sda (512GB SSD - HS-SSD-L100)

分区表：msdos（MBR）
├─ /dev/sda1 (EFI/Boot)  537MB  (fat32)
└─ /dev/sda5 (Root)      468GB  (ext4)
   ├─ 已用：133GB (28%)
   └─ 可用：312GB (72%) ← 重要！
```

### 空间评估

```
当前 Ubuntu 20.04 占用：133GB
可用空间：312GB

建议分配方案：
┌─────────────────────────────────┐
│ 缩小 20.04 到：350GB             │
│ 预留给 22.04：150GB              │
│ 总计需要：500GB                  │
│ 实际有：  512GB 总容量           │
│ 最终可用：12GB 余量              │
└─────────────────────────────────┘
```

### ⚠️ 存在的问题

1. **分区表是 MBR（msdos），不是 GPT**
   - MBR 最多支持 4 个主分区
   - 当前有：1 个主分区 + 1 个扩展分区 + 1 个逻辑分区
   - 📍 **限制**：无法再创建新的主分区
   - 💡 **解决方案**：需要转换 MBR → GPT（见下面详细步骤）

2. **启动方式是 BIOS，不是 UEFI**
   - 这是 MBR 分区表的标志
   - 不影响双系统安装，但需要特殊处理

---

## 🎯 安装可行性判断

| 检查项 | 结果 | 备注 |
|--------|------|------|
| **磁盘大小** | ✅ 足够 | 312GB 可用 >> 150GB 所需 |
| **RAM** | ✅ 足够 | 15GB >> 8GB 推荐 |
| **GPU** | ✅ 完美 | RTX 3090 是 Isaac Lab 完美选择 |
| **CUDA** | ✅ 兼容 | 12.2 支持所有最新库 |
| **分区** | ⚠️ 需改造 | MBR→GPT 转换（技术难度：低-中） |
| **启动** | ✅ 支持 | BIOS 启动可以，但 UEFI 更安全 |

---

## 🚀 推荐方案

### 方案 A：直接分配（最简单，风险小）✅ 推荐

**不转换 MBR→GPT，直接在逻辑分区中安装 22.04**

步骤：
1. 缩小 `/dev/sda5`（现在 468GB）→ 350GB
2. 创建新的逻辑分区：150GB
3. Ubuntu 22.04 安装在新逻辑分区
4. Grub 引导两个系统

**优点**：
- 无需转换分区表（零风险）
- 两个系统都在逻辑分区中（都能启动）
- 缺点少

**缺点**：
- MBR 有 4 分区限制（未来难以扩展）

### 方案 B：转换 MBR→GPT（更专业，可扩展）⚙️ 可选

**将 MBR 转换为 GPT，重新分配**

优点：
- 支持无限分区数
- 更现代、更安全
- 未来易于扩展

缺点：
- 技术难度高
- 风险更大（数据可能丢失）
- 需要 30-60 分钟

**建议**：如果你技术经验丰富，可以尝试。但首次建议用方案 A。

---

## 📋 实际操作步骤（方案 A）

### Step 1：备份数据（必做）

```bash
# 备份整个 DERL 项目
cd /home/t/yb
tar -czf agrimgupta_derl_backup_$(date +%Y%m%d_%H%M%S).tar.gz agrimgupta_derl/
# 检查大小
du -sh agrimgupta_derl_backup_*.tar.gz

# 备份其他重要文件
# ...
```

**预期时间**：20-30 分钟（取决于磁盘速度）

### Step 2：缩小 /dev/sda5 分区

```bash
# 装 GParted（图形界面，较安全）
sudo apt install gparted -y

# 启动 GParted
sudo gparted
```

在 GParted 中：
1. 找到 `/dev/sda5`（468GB）
2. 右键 → "Resize/Move"
3. 设置新大小：350GB（从 468GB 缩小）
4. 点击绿色 ✓ 按钮应用
5. **耐心等待** 30-60 分钟（进度条会显示）

```bash
# 完成后验证
sudo parted -l
# 应该看到：
# 5  539MB  376GB  ...  ext4  ← 新的大小 ~350GB
```

### Step 3：检查新的未分配空间

```bash
# 确认未分配空间
sudo parted -l | grep -A 20 "Disk /dev/sda"

# 应该看到：
# Number  Start   End    Size   Type      File system
# 1       ...     ...    ...    primary   fat32
# 5       ...     376GB  ...    logical   ext4
# (空白行) 376GB  512GB  ~136GB           ← 未分配空间
```

### Step 4：制作 Ubuntu 22.04 启动 U 盘

```bash
# 下载 ISO 文件（在浏览器中）
# https://releases.ubuntu.com/jammy/
# ubuntu-22.04.3-desktop-amd64.iso (~3.4GB)

# 插入 U 盘（>= 4GB），查看设备
lsblk
# 找到 U 盘，比如 /dev/sdb

# 卸载 U 盘
sudo umount /dev/sdb*

# 写入 ISO（用 dd）
sudo dd if=~/Downloads/ubuntu-22.04.3-desktop-amd64.iso of=/dev/sdb bs=4M status=progress
sudo sync

# 或用 Etcher（图形界面）
# sudo snap install balena-etcher-electron
# 然后打开 Etcher，选择 ISO 和 U 盘
```

**预期时间**：10-20 分钟

### Step 5：重启并安装

```bash
# 重启
sudo reboot

# 在启动菜单按 F12（或 F2/DEL，取决于主板）选择 U 盘启动
```

在安装程序中：
- **语言**：English 或中文
- **更新选项**：✅ 勾选"安装第三方驱动"（会装 NVIDIA 驱动）
- **安装类型**：选择"Something else"（手动分区）
- **分区配置**：
  ```
  /dev/sda5 (缩小后的 350GB) → Ubuntu 20.04 保持不动
  /dev/sda6 (新建 150GB 分区)
    ├─ 文件系统：ext4
    ├─ 挂载点：/
    └─ 不勾选"为新 Ubuntu 安装安装启动程序"
  ```
- **启动程序位置**：`/dev/sda`（让 Grub 管理整个磁盘）
- **用户名**：t（和现在一样）
- **计算机名**：ubuntu-22-isaac（用于区分）

**预期时间**：30-40 分钟

### Step 6：完成安装后配置

```bash
# 系统会自动启动进 22.04
# 第一次启动可能需要 2-3 分钟（显示启动画面）

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装开发工具
sudo apt install build-essential python3.11 python3.11-dev python3.11-venv git -y

# 验证环境
python3 --version  # 应该是 3.11+
nvidia-smi         # 应该能看到 RTX 3090

# 验证两个系统都能启动（重启并选择 Ubuntu 20.04）
sudo reboot
# 在 Grub 菜单中选择 "Ubuntu 20.04" 或 "Advanced options"
```

---

## ⏱️ 时间估算

| 步骤 | 耗时 | 备注 |
|------|------|------|
| 备份 | 20-30 分钟 | 取决于磁盘速度 |
| 分区缩小 | 30-60 分钟 | **最长的步骤** |
| 制作启动盘 | 10-20 分钟 | 写入 ISO |
| 安装 22.04 | 30-40 分钟 | 自动化过程 |
| 系统配置 | 15-20 分钟 | pip 更新等 |
| **总计** | **2-3.5 小时** | 其中大部分是自动过程 |

---

## ✅ 最终结论

| 项目 | 判断 |
|------|------|
| **可行性** | ✅ 完全可行 |
| **难度** | ⭐⭐☆☆☆ 中等偏低 |
| **风险** | 🟢 低（按步骤做） |
| **推荐** | ✅ 强烈推荐方案 A |
| **预期结果** | Ubuntu 20.04 + Ubuntu 22.04 双启动 |

---

## 🛟 如果出错怎么办？

### Q：分区缩小失败？
- 在 GParted 中按 Ctrl+Z 撤销
- 或关闭 GParted（所有更改未应用）

### Q：安装卡住了？
- 用 U 盘重启
- 尝试安装程序中的"修复"选项

### Q：装完后无法启动？
- 用 20.04 启动盘启动
- 用 `fsck` 修复磁盘错误
- 或恢复备份

### Q：Grub 菜单无法选择 20.04？
- 在 22.04 中运行：
  ```bash
  sudo os-prober
  sudo grub-mkconfig -o /boot/grub/grub.cfg
  ```

---

## 📞 下一步

1. ✅ 准备好了吗？我可以给你更详细的 GParted 截图指导
2. ⏸️ 想先备份？我可以帮你写个备份脚本
3. ❓ 有其他问题？随时问我

**建议**：先读完这份报告，再开始操作。不着急！
